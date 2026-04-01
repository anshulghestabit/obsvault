from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.helpers import (
    choose_output_path_from_query,
    extract_count_requirements,
    extract_expected_sections_from_query,
    infer_deliverable_mode,
    infer_depth_threshold,
)
from nexus_ai.models import (
    ArtifactRecord,
    ArtifactRequirement,
    CompletionCheckInput,
    CompletionCheckResult,
    ContractRequest,
    FulfillmentContract,
)


class CompletionCheckerAgent(NexusBaseAgent):
    def _infer_semantic_requirements(self, query: str) -> list[str]:
        q = query.lower()
        semantic: list[str] = []

        if "pipeline" in q:
            semantic.extend(["stages", "flow", "components"])

        if "rag" in q or "retrieval augmented generation" in q:
            semantic.extend(
                [
                    "ingestion",
                    "chunking",
                    "embedding",
                    "indexing",
                    "retrieval",
                    "augmentation",
                    "generation",
                ]
            )

        if "architecture" in q:
            semantic.extend(["components", "data flow", "deployment", "tradeoffs"])

        if "training module" in q or "curriculum" in q:
            semantic.extend(["week", "day", "topics", "exercise", "deliverables"])

        if "strategy" in q or "roadmap" in q or "plan" in q:
            semantic.extend(["phases", "risks", "milestones", "execution"])

        cleaned: list[str] = []
        for item in semantic:
            if item not in cleaned:
                cleaned.append(item)
        return cleaned

    def _heuristic_contract(self, query: str, task_type: str, output_path: str) -> FulfillmentContract:
        resolved_output = output_path or choose_output_path_from_query(query)
        deliverable_mode = infer_deliverable_mode(task_type, query, resolved_output)
        expected_sections = extract_expected_sections_from_query(query)
        expected_sections.extend(self._infer_semantic_requirements(query))

        deduped_sections: list[str] = []
        for item in expected_sections:
            if item not in deduped_sections:
                deduped_sections.append(item)

        count_requirements = extract_count_requirements(query)
        requested_folder = Path(resolved_output).parent.name if resolved_output else ""
        must_create_new_folder = "new folder" in query.lower() and bool(requested_folder)

        artifact_requirements: list[ArtifactRequirement] = []
        if resolved_output:
            artifact_requirements.append(
                ArtifactRequirement(
                    name="primary_output",
                    path_hint=resolved_output,
                    format=Path(resolved_output).suffix.lower(),
                    must_exist=True,
                    description="Primary deliverable requested by the user.",
                )
            )

        structural_requirements = []
        if deduped_sections:
            structural_requirements.append("include explicitly requested sections and semantic components")
        if count_requirements:
            structural_requirements.append("satisfy quantified requirements from the prompt")
        if must_create_new_folder:
            structural_requirements.append("honor the user-requested new folder location")

        return FulfillmentContract(
            task_summary=query[:300],
            deliverable_mode=deliverable_mode,
            requested_output_path=resolved_output,
            requested_folder=requested_folder,
            must_create_new_folder=must_create_new_folder,
            structural_requirements=structural_requirements,
            count_requirements=count_requirements,
            expected_sections=deduped_sections,
            min_depth_chars=infer_depth_threshold(task_type, query),
            artifact_requirements=artifact_requirements,
            success_criteria=[
                "directly answers the task",
                "is sufficiently detailed for the scope",
                "saves the requested artifact when requested",
                "covers the required semantic components of the task",
            ],
        )

    @message_handler
    async def handle_contract_request(self, message: ContractRequest, ctx: MessageContext) -> FulfillmentContract:
        self._logger.add(
            "completion_checker",
            "contract_start",
            {
                "query": message.query,
                "task_type": message.task_type,
                "output_path": message.output_path,
            },
        )

        heuristic = self._heuristic_contract(message.query, message.task_type, message.output_path)

        system_prompt = (
            "You are the Completion Checker in NEXUS AI. "
            "Extract a generic fulfillment contract from the user task. "
            "Return JSON only with keys: "
            "task_summary, deliverable_mode, structural_requirements, count_requirements, expected_sections, min_depth_chars, success_criteria, must_create_new_folder. "
            "Be strict about semantic completeness. "
            "Do not assume a specific domain unless the user asks for one."
        )
        user_prompt = (
            f"Query:\n{message.query}\n\n"
            f"Task type:\n{message.task_type}\n\n"
            f"Resolved output path:\n{message.output_path}\n\n"
            f"Heuristic contract:\n{asdict(heuristic)}"
        )

        data = await self._llm_json(system_prompt, user_prompt)

        contract = FulfillmentContract(
            task_summary=str(data.get("task_summary", heuristic.task_summary)),
            deliverable_mode=str(data.get("deliverable_mode", heuristic.deliverable_mode)),
            requested_output_path=heuristic.requested_output_path,
            requested_folder=heuristic.requested_folder,
            must_create_new_folder=bool(data.get("must_create_new_folder", heuristic.must_create_new_folder)),
            structural_requirements=list(data.get("structural_requirements", heuristic.structural_requirements)),
            count_requirements=dict(data.get("count_requirements", heuristic.count_requirements)),
            expected_sections=list(data.get("expected_sections", heuristic.expected_sections)),
            min_depth_chars=int(data.get("min_depth_chars", heuristic.min_depth_chars)),
            artifact_requirements=heuristic.artifact_requirements,
            success_criteria=list(data.get("success_criteria", heuristic.success_criteria)),
        )

        self._logger.add(
            "completion_checker",
            "contract_finish",
            {"contract": asdict(contract)},
        )
        return contract

    def _collect_artifact_records(self, worker_outputs, contract: FulfillmentContract) -> list[ArtifactRecord]:
        records: dict[str, ArtifactRecord] = {}

        def add_record(name: str, path_str: str, created_by: str) -> None:
            if not path_str:
                return
            path = Path(path_str)
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            records[str(path.resolve())] = ArtifactRecord(
                name=name,
                path=str(path.resolve()),
                exists=exists,
                size_bytes=size,
                created_by=created_by,
                status="verified" if exists and size > 0 else "missing",
            )

        for output in worker_outputs:
            for key in ["saved_path", "document_saved_path", "final_saved_path", "file_path", "tool_file_path"]:
                value = output.artifacts.get(key)
                if isinstance(value, str) and value.strip():
                    add_record(key, value, output.owner)

            for value in output.artifacts_created:
                if isinstance(value, str) and value.strip():
                    add_record("artifact_created", value, output.owner)

        if contract.requested_output_path:
            add_record("requested_output", contract.requested_output_path, "requested")

        return list(records.values())

    def _count_in_draft(self, unit: str, draft: str, artifact_records: list[ArtifactRecord]) -> int:
        lower = draft.lower()

        if unit == "week":
            return len(set(re.findall(r"\bweek\s+\d+\b", lower)))
        if unit == "day":
            return len(set(re.findall(r"\bday\s+\d+\b", lower)))
        if unit == "file":
            return sum(1 for record in artifact_records if record.exists)
        if unit == "section":
            return len(re.findall(r"^#+\s+.+$", draft, flags=re.MULTILINE))
        if unit == "agent":
            return len(set(re.findall(r"\bagent\b", lower)))
        return 0

    def _section_satisfied(self, section: str, draft: str) -> bool:
        section = section.lower().strip()
        lower = draft.lower()

        if section in lower:
            return True

        tokens = [t for t in re.findall(r"[a-zA-Z]{4,}", section)]
        if not tokens:
            return False

        # More strict than before: require meaningful token match.
        matched = sum(1 for token in tokens if token in lower)
        return matched >= max(1, min(2, len(tokens)))

    @message_handler
    async def handle_completion_check(self, message: CompletionCheckInput, ctx: MessageContext) -> CompletionCheckResult:
        self._logger.add(
            "completion_checker",
            "check_start",
            {
                "query": message.query,
                "task_type": message.task_type,
            },
        )

        contract = message.contract
        artifact_records = self._collect_artifact_records(message.worker_outputs, contract)
        draft = message.draft or ""

        missing_requirements: list[str] = []
        satisfied_requirements: list[str] = []
        task_satisfaction: dict[str, bool] = {}

        if contract.requested_output_path:
            matching = [r for r in artifact_records if Path(r.path).resolve() == Path(contract.requested_output_path).resolve()]
            ok = any(r.exists and r.size_bytes > 0 for r in matching)
            task_satisfaction["requested_output_exists"] = ok
            if ok:
                satisfied_requirements.append("requested output artifact exists")
            else:
                missing_requirements.append("requested output artifact was not created or is empty")

        if contract.must_create_new_folder and contract.requested_folder:
            ok = any(Path(r.path).parent.name == contract.requested_folder and r.exists for r in artifact_records)
            task_satisfaction["requested_folder_honored"] = ok
            if ok:
                satisfied_requirements.append("requested folder location was honored")
            else:
                missing_requirements.append("requested folder location was not honored")

        depth_ok = len(draft.strip()) >= contract.min_depth_chars
        task_satisfaction["depth_ok"] = depth_ok
        if depth_ok:
            satisfied_requirements.append("response depth is sufficient")
        else:
            missing_requirements.append(
                f"response is too shallow for the task scope (need about {contract.min_depth_chars}+ characters of substantive content)"
            )

        for section in contract.expected_sections:
            ok = self._section_satisfied(section, draft)
            task_satisfaction[f"section::{section}"] = ok
            if ok:
                satisfied_requirements.append(f"section covered: {section}")
            else:
                missing_requirements.append(f"missing requested section or semantic component: {section}")

        for unit, required_count in contract.count_requirements.items():
            actual = self._count_in_draft(unit, draft, artifact_records)
            ok = actual >= required_count
            task_satisfaction[f"count::{unit}"] = ok
            if ok:
                satisfied_requirements.append(f"count satisfied for {unit}: {actual}/{required_count}")
            else:
                missing_requirements.append(f"count requirement not satisfied for {unit}: found {actual}, expected {required_count}")

        fulfilled = len(missing_requirements) == 0
        summary = "Fulfillment contract satisfied." if fulfilled else "Fulfillment contract has unmet requirements."

        result = CompletionCheckResult(
            fulfilled=fulfilled,
            missing_requirements=missing_requirements,
            satisfied_requirements=satisfied_requirements,
            artifact_records=artifact_records,
            task_satisfaction=task_satisfaction,
            summary=summary,
        )

        self._logger.add(
            "completion_checker",
            "check_finish",
            {
                "fulfilled": result.fulfilled,
                "missing_requirements": result.missing_requirements,
                "artifact_records": [asdict(r) for r in result.artifact_records],
            },
        )
        return result