from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from autogen_core import AgentId, MessageContext, message_handler

from memory.session_memory import SessionMemory
from memory.vector_store import FaissVectorStore
from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.helpers import (
    build_memory_context,
    choose_output_path_from_query,
    ensure_safe_output_path,
    request_wants_file_output,
)
from nexus_ai.logger import NexusLogger
from nexus_ai.models import (
    CompletionCheckInput,
    ContractRequest,
    CritiqueInput,
    NexusResult,
    NexusTask,
    OptimizationInput,
    ReportInput,
    ValidationInput,
    WorkerInput,
    WorkerOutput,
)
from tools.file_agent import write_text_file


def _print_agent_banner(agent: str, phase: str, detail: str = "") -> None:
    width = 72
    top = "╔" + "═" * (width - 2) + "╗"
    bot = "╚" + "═" * (width - 2) + "╝"
    body = f"║  [{agent.upper()}]  →  {phase}"
    body = body + " " * (width - len(body) - 1) + "║"
    print(f"\n{top}")
    print(body)
    if detail:
        clipped = str(detail)[: width - 7]
        det_line = f"║     {clipped}"
        det_line = det_line + " " * (width - len(det_line) - 1) + "║"
        print(det_line)
    print(bot)


class OrchestratorAgent(NexusBaseAgent):
    def __init__(
        self,
        name: str,
        model_client,
        nexus_logger: NexusLogger,
        session_memory: SessionMemory,
        vector_store: FaissVectorStore,
        debug_mode: bool = False,
    ) -> None:
        super().__init__(name, model_client, nexus_logger, debug_mode)
        self._session_memory = session_memory
        self._vector_store = vector_store

    def _normalize_issue_text(self, issue) -> str:
        if isinstance(issue, str):
            return issue
        if isinstance(issue, dict):
            if "issue" in issue:
                return str(issue["issue"])
            if "message" in issue:
                return str(issue["message"])
            return json.dumps(issue, ensure_ascii=False)
        if isinstance(issue, list):
            return ", ".join(str(x) for x in issue)
        return str(issue)

    def _normalize_issue_list(self, issues) -> list[str]:
        if not issues:
            return []
        normalized = [self._normalize_issue_text(issue).strip() for issue in issues]
        return [item for item in normalized if item]

    async def _dispatch_step(
        self,
        run_id: str,
        query: str,
        step,
        memory_context: str,
        task_type: str,
        target_file: str,
        output_path: str,
        owner_override: str | None = None,
    ) -> WorkerOutput:
        owner = owner_override or step.owner
        target = {
            "researcher": "researcher",
            "coder": "coder",
            "analyst": "analyst",
        }.get(owner, "researcher")

        self._logger.add(
            "orchestrator",
            "dispatch_step",
            {
                "run_id": run_id,
                "step_id": step.step_id,
                "owner": owner,
                "original_owner": step.owner,
                "title": step.title,
                "task_type": task_type,
                "target_file": target_file,
                "output_path": output_path,
                "depends_on": getattr(step, "depends_on", []),
                "can_run_parallel": getattr(step, "can_run_parallel", False),
            },
        )

        return await self.send_message(
            WorkerInput(
                original_query=query,
                step=step,
                memory_context=memory_context,
                task_type=task_type,
                target_file=target_file,
                output_path=output_path,
            ),
            AgentId(target, "default"),
        )

    def _normalize_output(self, item, step) -> WorkerOutput:
        if isinstance(item, Exception):
            self._logger.add(
                "orchestrator",
                "worker_exception",
                {
                    "step_id": step.step_id,
                    "owner": step.owner,
                    "title": step.title,
                    "error": str(item),
                },
            )
            return WorkerOutput(
                step_id=step.step_id,
                owner=step.owner,
                title=step.title,
                result=f"Failure recovered with placeholder: {str(item)}",
                artifacts={"execution_passed": False},
                status="failed",
                confidence=0.1,
                retry_hint=str(item),
            )

        self._logger.add(
            "orchestrator",
            "worker_result_received",
            {
                "step_id": item.step_id,
                "owner": item.owner,
                "title": item.title,
                "status": item.status,
                "result_preview": item.result[:500],
            },
        )
        return item

    async def _run_step_with_fallbacks(
        self,
        run_id: str,
        query: str,
        step,
        memory_context: str,
        task_type: str,
        target_file: str,
        output_path: str,
        retry_suffix: str = "",
    ) -> WorkerOutput:
        candidate_owners = [step.owner] + [o for o in getattr(step, "fallback_owners", []) if o != step.owner]
        final_query = query if not retry_suffix else f"{query}\n\nRetry guidance:\n{retry_suffix}"

        for idx, owner in enumerate(candidate_owners):
            try:
                if idx == 0:
                    _print_agent_banner(owner, f"Step {step.step_id} — {step.title}", f"Instruction: {step.instruction[:80]}...")
                else:
                    _print_agent_banner(owner, f"Fallback handoff for Step {step.step_id} — {step.title}", f"Trying alternate owner: {owner}")

                output = await self._dispatch_step(
                    run_id=run_id,
                    query=final_query,
                    step=step,
                    memory_context=memory_context,
                    task_type=task_type,
                    target_file=target_file,
                    output_path=output_path,
                    owner_override=owner,
                )

                if owner != step.owner:
                    output = WorkerOutput(
                        step_id=output.step_id,
                        owner=step.owner,
                        title=output.title,
                        result=output.result,
                        artifacts={**output.artifacts, "handled_by": owner},
                        status=output.status,
                        confidence=output.confidence,
                        tool_calls=output.tool_calls,
                        tool_results=output.tool_results,
                        grounding_sources=output.grounding_sources,
                        artifacts_created=output.artifacts_created,
                        needs_handoff=output.needs_handoff,
                        handoff_target=output.handoff_target,
                        retry_hint=output.retry_hint,
                    )

                if output.artifacts.get("execution_passed") is False and idx < len(candidate_owners) - 1:
                    self._logger.add(
                        "orchestrator",
                        "handoff_triggered",
                        {
                            "run_id": run_id,
                            "step_id": step.step_id,
                            "from_owner": owner,
                            "to_owner": candidate_owners[idx + 1],
                            "reason": "execution_passed=False",
                        },
                    )
                    continue

                return output
            except Exception as exc:
                self._logger.add(
                    "orchestrator",
                    "worker_exception",
                    {
                        "run_id": run_id,
                        "step_id": step.step_id,
                        "owner": owner,
                        "title": step.title,
                        "error": str(exc),
                    },
                )

        return WorkerOutput(
            step_id=step.step_id,
            owner=step.owner,
            title=step.title,
            result="All attempts failed for this step.",
            artifacts={"execution_passed": False},
            status="failed",
            confidence=0.1,
            retry_hint="Fallback owners were exhausted.",
        )

    async def _execute_in_dependency_waves(
        self,
        run_id: str,
        query: str,
        steps: list,
        memory_context: str,
        task_type: str,
        target_file: str,
        output_path: str,
    ) -> list[WorkerOutput]:
        pending = {getattr(step, "step_id", idx + 1): step for idx, step in enumerate(steps)}
        completed: dict[int, WorkerOutput] = {}
        outputs: list[WorkerOutput] = []
        wave_number = 0

        while pending:
            ready_steps = [
                step for _, step in pending.items()
                if all(dep in completed for dep in getattr(step, "depends_on", []))
            ]

            if not ready_steps:
                for step_id, step in pending.items():
                    failed = WorkerOutput(
                        step_id=getattr(step, "step_id", step_id),
                        owner=getattr(step, "owner", "unknown"),
                        title=getattr(step, "title", "Untitled"),
                        result="Step could not run because dependencies were unresolved.",
                        artifacts={"execution_passed": False, "deadlock": True},
                        status="failed",
                        confidence=0.1,
                    )
                    completed[getattr(step, "step_id", step_id)] = failed
                    outputs.append(failed)
                break

            wave_number += 1
            self._logger.add(
                "orchestrator",
                "wave_ready",
                {
                    "run_id": run_id,
                    "wave_number": wave_number,
                    "steps": [
                        {
                            "step_id": step.step_id,
                            "owner": step.owner,
                            "title": step.title,
                            "depends_on": step.depends_on,
                            "can_run_parallel": step.can_run_parallel,
                        }
                        for step in ready_steps
                    ],
                },
            )

            tasks = [
                self._run_step_with_fallbacks(
                    run_id=run_id,
                    query=query,
                    step=step,
                    memory_context=memory_context,
                    task_type=task_type,
                    target_file=target_file,
                    output_path=output_path,
                )
                for step in ready_steps
            ]
            raw_outputs = await asyncio.gather(*tasks, return_exceptions=True)

            for step, raw in zip(ready_steps, raw_outputs):
                normalized = self._normalize_output(raw, step)
                completed[getattr(step, "step_id", -1)] = normalized
                outputs.append(normalized)
                pending.pop(getattr(step, "step_id", -1), None)

        outputs.sort(key=lambda x: x.step_id)
        return outputs

    def _find_verified_saved_artifact(self, worker_outputs: list[WorkerOutput]) -> str:
        for output in worker_outputs:
            for key in ["saved_path", "document_saved_path", "final_saved_path", "file_path", "tool_file_path"]:
                path = output.artifacts.get(key)
                if path and Path(path).exists() and Path(path).stat().st_size > 0:
                    return str(Path(path).resolve())
        return ""

    def _persist_text_artifact(self, output_path: str, content: str, step_id: int, title: str) -> WorkerOutput:
        resolved = ensure_safe_output_path(output_path)
        Path(resolved).parent.mkdir(parents=True, exist_ok=True)
        write_text_file(resolved, content)

        exists = Path(resolved).exists() and Path(resolved).stat().st_size > 0

        return WorkerOutput(
            step_id=step_id,
            owner="orchestrator",
            title=title,
            result=f"Persisted artifact: {resolved}" if exists else f"Failed to persist artifact: {resolved}",
            artifacts={
                "mode": "final_document",
                "saved_path": resolved,
                "final_saved_path": resolved,
                "execution_passed": exists,
            },
            confidence=1.0 if exists else 0.1,
            tool_calls=["write_text_file"],
            artifacts_created=[resolved] if exists else [],
        )

    async def _retry_targeted_steps(
        self,
        run_id: str,
        query: str,
        retry_targets: list[str],
        plan_steps: list,
        existing_outputs: list[WorkerOutput],
        memory_context: str,
        task_type: str,
        target_file: str,
        output_path: str,
        issues: list[str],
    ) -> list[WorkerOutput]:
        retry_steps = [step for step in plan_steps if step.owner in retry_targets]
        if not retry_steps:
            retry_steps = plan_steps

        retry_suffix = "\n".join(self._normalize_issue_list(issues)[:10])
        retried_outputs: list[WorkerOutput] = []

        for step in retry_steps:
            retried = await self._run_step_with_fallbacks(
                run_id=run_id,
                query=query,
                step=step,
                memory_context=memory_context,
                task_type=task_type,
                target_file=target_file,
                output_path=output_path,
                retry_suffix=retry_suffix,
            )
            retried_outputs.append(retried)

        outputs_by_step = {o.step_id: o for o in existing_outputs}
        for retried in retried_outputs:
            outputs_by_step[retried.step_id] = retried

        final_outputs = list(outputs_by_step.values())
        final_outputs.sort(key=lambda x: x.step_id)
        return final_outputs

    @message_handler
    async def handle_task(self, message: NexusTask, ctx: MessageContext) -> NexusResult:
        run_id = uuid.uuid4().hex[:12]

        _print_agent_banner(
            "orchestrator",
            "Task received — building memory context & routing to agents",
            f"Run ID: {run_id} | Query: {message.query[:60]}...",
        )
        self._logger.add("orchestrator", "start", {"run_id": run_id, "query": message.query})

        memory_context = build_memory_context(message.query, self._session_memory, self._vector_store)
        self._logger.add(
            "orchestrator",
            "memory_context_built",
            {
                "run_id": run_id,
                "preview": memory_context[:1000],
            },
        )

        _print_agent_banner("planner", "Analysing task and building an execution graph")
        plan = await self.send_message(message, AgentId("planner", "default"))
        raw_output_path = plan.output_path or choose_output_path_from_query(message.query)
        resolved_output_path = ensure_safe_output_path(raw_output_path) if raw_output_path else ""

        contract = await self.send_message(
            ContractRequest(
                query=message.query,
                task_type=plan.task_type,
                output_path=resolved_output_path,
            ),
            AgentId("completion_checker", "default"),
        )

        self._logger.add(
            "orchestrator",
            "plan_received",
            {
                "run_id": run_id,
                "task_type": plan.task_type,
                "target_file": plan.target_file,
                "output_path": resolved_output_path,
                "planning_notes": plan.planning_notes,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "owner": step.owner,
                        "title": step.title,
                        "depends_on": step.depends_on,
                        "can_run_parallel": step.can_run_parallel,
                    }
                    for step in plan.steps
                ],
            },
        )

        worker_outputs = await self._execute_in_dependency_waves(
            run_id=run_id,
            query=message.query,
            steps=plan.steps,
            memory_context=memory_context,
            task_type=plan.task_type,
            target_file=plan.target_file,
            output_path=resolved_output_path,
        )

        _print_agent_banner("critic", "Evaluating worker outputs for risks & gaps")
        critique = await self.send_message(
            CritiqueInput(
                query=message.query,
                task_type=plan.task_type,
                plan=plan.steps,
                worker_outputs=worker_outputs,
            ),
            AgentId("critic", "default"),
        )

        _print_agent_banner("optimizer", "Synthesising an improved draft from all worker outputs")
        optimizer = await self.send_message(
            OptimizationInput(
                query=message.query,
                task_type=plan.task_type,
                worker_outputs=worker_outputs,
                critique=critique.critique,
            ),
            AgentId("optimizer", "default"),
        )

        wants_file_output = request_wants_file_output(message.query)
        verified_saved_path = self._find_verified_saved_artifact(worker_outputs)

        if wants_file_output and not verified_saved_path and contract.requested_output_path:
            worker_outputs.append(
                self._persist_text_artifact(
                    contract.requested_output_path,
                    optimizer.improved_draft,
                    step_id=999,
                    title="Persist optimized draft artifact before validation",
                )
            )

        completion = await self.send_message(
            CompletionCheckInput(
                query=message.query,
                task_type=plan.task_type,
                draft=optimizer.improved_draft,
                worker_outputs=worker_outputs,
                plan=plan.steps,
                contract=contract,
            ),
            AgentId("completion_checker", "default"),
        )

        _print_agent_banner("validator", "Checking draft for correctness, completeness & quality")
        validator = await self.send_message(
            ValidationInput(
                query=message.query,
                task_type=plan.task_type,
                draft=optimizer.improved_draft,
                worker_outputs=worker_outputs,
                plan=plan.steps,
                contract=contract,
                completion=completion,
            ),
            AgentId("validator", "default"),
        )

        normalized_validator_issues = self._normalize_issue_list(validator.issues)

        self._logger.add(
            "orchestrator",
            "validation_result",
            {
                "run_id": run_id,
                "passed": validator.passed,
                "score": validator.score,
                "issues": normalized_validator_issues,
                "retry_targets": validator.retry_targets,
            },
        )

        if validator.needs_retry and validator.retry_targets:
            worker_outputs = await self._retry_targeted_steps(
                run_id=run_id,
                query=message.query,
                retry_targets=validator.retry_targets,
                plan_steps=plan.steps,
                existing_outputs=worker_outputs,
                memory_context=memory_context,
                task_type=plan.task_type,
                target_file=plan.target_file,
                output_path=resolved_output_path,
                issues=normalized_validator_issues,
            )

            optimizer = await self.send_message(
                OptimizationInput(
                    query=message.query,
                    task_type=plan.task_type,
                    worker_outputs=worker_outputs,
                    critique=critique.critique,
                ),
                AgentId("optimizer", "default"),
            )

            if wants_file_output and not self._find_verified_saved_artifact(worker_outputs) and contract.requested_output_path:
                worker_outputs.append(
                    self._persist_text_artifact(
                        contract.requested_output_path,
                        optimizer.improved_draft,
                        step_id=1000,
                        title="Persist optimized draft artifact after retry",
                    )
                )

            completion = await self.send_message(
                CompletionCheckInput(
                    query=message.query,
                    task_type=plan.task_type,
                    draft=optimizer.improved_draft,
                    worker_outputs=worker_outputs,
                    plan=plan.steps,
                    contract=contract,
                ),
                AgentId("completion_checker", "default"),
            )

            validator = await self.send_message(
                ValidationInput(
                    query=message.query,
                    task_type=plan.task_type,
                    draft=optimizer.improved_draft,
                    worker_outputs=worker_outputs,
                    plan=plan.steps,
                    contract=contract,
                    completion=completion,
                ),
                AgentId("validator", "default"),
            )
            normalized_validator_issues = self._normalize_issue_list(validator.issues)

        _print_agent_banner("reporter", "Compiling the final answer and execution tree")
        report = await self.send_message(
            ReportInput(
                query=message.query,
                task_type=plan.task_type,
                plan=plan.steps,
                worker_outputs=worker_outputs,
                critique=critique.critique,
                improvements=optimizer.improvements,
                validated_answer=validator.validated_answer,
                contract=contract,
                completion=completion,
                artifact_records=completion.artifact_records,
            ),
            AgentId("reporter", "default"),
        )

        final_answer = report.final_answer
        final_saved_path = self._find_verified_saved_artifact(worker_outputs)

        if wants_file_output and contract.requested_output_path:
            final_persist = self._persist_text_artifact(
                contract.requested_output_path,
                final_answer,
                step_id=1001,
                title="Persist final report artifact",
            )
            self._logger.add(
                "orchestrator",
                "final_artifact_save_attempt",
                {
                    "run_id": run_id,
                    "requested": True,
                    "output_path": contract.requested_output_path,
                    "saved_ok": final_persist.artifacts.get("execution_passed"),
                    "saved_path": final_persist.artifacts.get("saved_path"),
                },
            )
            if final_persist.artifacts.get("execution_passed"):
                final_saved_path = str(final_persist.artifacts.get("saved_path"))
                if "Saved output file:" not in final_answer:
                    final_answer += f"\n\nSaved output file: {final_saved_path}"

        validation_issues = self._normalize_issue_list(validator.issues)

        if final_saved_path and Path(final_saved_path).exists() and Path(final_saved_path).stat().st_size > 0:
            validation_issues = [
                issue for issue in validation_issues
                if "saved artifact was produced" not in issue.lower()
            ]

        self._session_memory.add_turn("user", message.query)
        self._session_memory.add_turn("assistant", final_answer)
        self._session_memory.store_facts(self._session_memory.extract_important_facts(message.query))
        self._session_memory.store_facts(self._session_memory.extract_important_facts(final_answer))
        self._vector_store.add_text(message.query, {"role": "user", "run_id": run_id})
        self._vector_store.add_text(final_answer, {"role": "assistant", "run_id": run_id})

        self._logger.add(
            "orchestrator",
            "finish",
            {
                "run_id": run_id,
                "saved_path": final_saved_path,
                "validation_issues": validation_issues,
            },
        )
        log_path = self._logger.flush(task_name="nexus_ai")

        return NexusResult(
            final_answer=final_answer,
            execution_tree=report.execution_tree,
            validation_issues=validation_issues,
            log_path=log_path,
        )