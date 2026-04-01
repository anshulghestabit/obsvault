from __future__ import annotations

import re
from pathlib import Path

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.helpers import infer_deliverable_mode
from nexus_ai.models import ValidationInput, ValidationResult


class ValidatorAgent(NexusBaseAgent):
    def _derive_retry_targets(self, issues: list[str], plan) -> list[str]:
        targets: set[str] = set()
        text = " ".join(issues).lower()

        for issue in issues:
            m = re.search(r"Missing expected worker outputs from: (.+)", issue)
            if m:
                owners = [item.strip() for item in m.group(1).split(",")]
                targets.update(owners)

        if any(k in text for k in ["artifact", "saved file", "output path", "folder", "created"]):
            targets.add("coder")

        if any(k in text for k in ["shallow", "missing requested section", "missing requested section or semantic component", "structure", "depth", "count requirement"]):
            targets.update({"optimizer", "researcher", "coder"})

        if any(k in text for k in ["execution", "syntax", "failed"]):
            targets.add("coder")

        if not targets and plan:
            targets.update(step.owner for step in plan)

        return sorted(targets)

    @message_handler
    async def handle_input(self, message: ValidationInput, ctx: MessageContext) -> ValidationResult:
        self._logger.add(
            "validator",
            "start",
            {
                "task_type": message.task_type,
                "query": message.query,
            },
        )

        issues: list[str] = []
        artifact_checks: dict[str, object] = {}
        grounding_checks: dict[str, object] = {}
        completeness_checks: dict[str, object] = {}

        produced_owners = {o.owner for o in message.worker_outputs}
        expected_owners = {step.owner for step in message.plan} if message.plan else set()

        missing_owners = sorted(expected_owners - produced_owners)
        if missing_owners:
            issues.append(f"Missing expected worker outputs from: {', '.join(missing_owners)}")

        for output in message.worker_outputs:
            if output.artifacts.get("execution_passed") is False:
                issues.append(f"{output.owner} step '{output.title}' failed execution.")
            if output.status == "failed":
                issues.append(f"{output.owner} step '{output.title}' returned failed status.")
            if not output.result or len(output.result.strip()) < 20:
                issues.append(f"{output.owner} step '{output.title}' produced too little usable output.")

        contract = message.contract
        completion = message.completion

        if contract is not None:
            artifact_checks["requested_output_path"] = contract.requested_output_path
            artifact_checks["deliverable_mode"] = contract.deliverable_mode
            completeness_checks["min_depth_chars"] = contract.min_depth_chars

            if contract.deliverable_mode == "code":
                coder = next((o for o in message.worker_outputs if o.owner == "coder"), None)
                if coder is None:
                    issues.append("Coder output missing for code-oriented task.")
                else:
                    saved_path = coder.artifacts.get("saved_path")
                    artifact_checks["code_saved_path"] = saved_path
                    if not saved_path or not Path(saved_path).exists():
                        issues.append("Generated or revised code file was not saved.")
                    if coder.artifacts.get("execution_passed") is not True:
                        issues.append("Generated or revised code did not pass execution validation.")

            # Critical check: document requests should not pass if coder emitted code-like content.
            if contract.deliverable_mode == "document":
                coder = next((o for o in message.worker_outputs if o.owner == "coder"), None)
                if coder:
                    text = coder.result.strip().lower()
                    code_markers = ["import ", "def ", "class ", "from ", "if __name__", "print("]
                    if any(marker in text for marker in code_markers) and not text.lstrip().startswith("#"):
                        issues.append("Document-style task appears to contain code-oriented output instead of a proper structured document.")

        if completion is not None:
            artifact_checks["artifact_records"] = [
                {"path": a.path, "exists": a.exists, "status": a.status}
                for a in completion.artifact_records
            ]
            completeness_checks["task_satisfaction"] = completion.task_satisfaction
            if not completion.fulfilled:
                issues.extend(completion.missing_requirements)

        deliverable_mode = infer_deliverable_mode(
            message.task_type,
            message.query,
            contract.requested_output_path if contract else "",
        )

        if deliverable_mode == "document" and len(message.draft.strip()) < 200:
            issues.append("Document-style answer is too short to be reliable.")

        retry_targets = self._derive_retry_targets(sorted(set(issues)), message.plan)
        score = max(0.0, 1.0 - (0.10 * len(set(issues))))

        if issues:
            result = ValidationResult(
                passed=False,
                issues=sorted(set(issues)),
                validated_answer=message.draft,
                score=score,
                needs_retry=True,
                retry_targets=retry_targets,
                artifact_checks=artifact_checks,
                grounding_checks=grounding_checks,
                completeness_checks=completeness_checks,
            )
        else:
            system_prompt = (
                "You are the Validator in NEXUS AI. "
                "Check the answer for clarity, directness, correctness, completeness, and obvious mistakes. "
                "Return JSON only with keys: passed, issues, validated_answer, score, needs_retry, retry_targets."
            )
            user_prompt = (
                f"Query:\n{message.query}\n\n"
                f"Task type:\n{message.task_type}\n\n"
                f"Draft answer:\n{message.draft}\n\n"
                f"Completion summary:\n{completion.summary if completion else 'N/A'}"
            )
            data = await self._llm_json(system_prompt, user_prompt)

            result = ValidationResult(
                passed=bool(data.get("passed", True)),
                issues=list(data.get("issues", [])),
                validated_answer=str(data.get("validated_answer", message.draft)),
                score=float(data.get("score", 0.92)),
                needs_retry=bool(data.get("needs_retry", False)),
                retry_targets=list(data.get("retry_targets", [])),
                artifact_checks=artifact_checks,
                grounding_checks=grounding_checks,
                completeness_checks=completeness_checks,
            )

        self._logger.add(
            "validator",
            "finish",
            {
                "passed": result.passed,
                "score": result.score,
                "issues": result.issues,
                "retry_targets": result.retry_targets,
            },
        )
        return result