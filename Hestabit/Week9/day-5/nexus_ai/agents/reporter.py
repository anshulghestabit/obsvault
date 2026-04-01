from __future__ import annotations

from pathlib import Path

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.models import ReportInput, ReportResult


class ReporterAgent(NexusBaseAgent):
    @message_handler
    async def handle_input(self, message: ReportInput, ctx: MessageContext) -> ReportResult:
        self._logger.add(
            "reporter",
            "start",
            {
                "task_type": message.task_type,
                "query": message.query,
            },
        )

        tree_lines = [f"User Query: {message.query}", "└── orchestrator", "    ├── planner"]
        for step in message.plan:
            parallel_note = " [parallel]" if getattr(step, "can_run_parallel", False) else ""
            tree_lines.append(f"    ├── {step.owner} -> {step.title}{parallel_note}")
        tree_lines.append("    ├── critic -> critique worker outputs")
        tree_lines.append("    ├── optimizer -> strengthen draft")
        tree_lines.append("    ├── completion_checker -> compare against fulfillment contract")
        tree_lines.append("    ├── validator -> validate final state")
        tree_lines.append("    └── reporter -> finalize response")

        if message.artifact_records:
            tree_lines.append("")
            tree_lines.append("Artifacts:")
            for artifact in message.artifact_records:
                status = "OK" if artifact.exists else "MISSING"
                tree_lines.append(f"  - {artifact.name}: {artifact.path} [{status}]")

        final_answer = message.validated_answer.strip()

        if message.completion is not None:
            final_answer += "\n\n## Fulfillment Status\n"
            final_answer += f"- Contract satisfied: {'Yes' if message.completion.fulfilled else 'No'}\n"
            if message.completion.satisfied_requirements:
                final_answer += "- Satisfied requirements:\n"
                for item in message.completion.satisfied_requirements[:12]:
                    final_answer += f"  - {item}\n"
            if message.completion.missing_requirements:
                final_answer += "- Remaining gaps:\n"
                for item in message.completion.missing_requirements[:12]:
                    final_answer += f"  - {item}\n"

        if message.artifact_records:
            final_answer += "\n## Artifact Manifest\n"
            for artifact in message.artifact_records:
                size = artifact.size_bytes if artifact.exists else 0
                final_answer += (
                    f"- {artifact.name}: {artifact.path} | exists={artifact.exists} | "
                    f"size={size} | created_by={artifact.created_by}\n"
                )

        code_output = next((o for o in message.worker_outputs if o.artifacts.get("mode") == "code_generation"), None)
        if code_output:
            exec_log = code_output.artifacts.get("execution_log", "")
            saved = code_output.artifacts.get("saved_path", "")
            if saved:
                final_answer += f"\nSaved file: {saved}"
            if exec_log:
                final_answer += f"\n\n## Execution Check\n{exec_log}"

        summary = (
            message.completion.summary
            if message.completion is not None
            else "Reported the validated answer with execution trace."
        )

        result = ReportResult(
            final_answer=final_answer,
            execution_tree="\n".join(tree_lines),
            summary=summary,
        )

        self._logger.add(
            "reporter",
            "finish",
            {"summary_preview": summary[:400]},
        )
        return result