from __future__ import annotations

from dataclasses import asdict

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.helpers import choose_output_path_from_query, choose_target_file_from_query, detect_task_type, request_wants_file_output
from nexus_ai.models import NexusTask, PlanResult, PlanStep


class PlannerAgent(NexusBaseAgent):
    def _build_generic_plan(self, query: str, task_type: str, output_path: str) -> list[PlanStep]:
        wants_file = request_wants_file_output(query) or bool(output_path)

        return [
            PlanStep(
                step_id=1,
                title="Clarify scope and success criteria",
                owner="researcher",
                instruction=(
                    f"Clarify the user's true intent, required structure, acceptance criteria, constraints, counts, "
                    f"and artifact expectations for: {query}"
                ),
                expected_output="structured task interpretation",
                success_checks=[
                    "task intent clarified",
                    "constraints identified",
                    "success criteria identified",
                ],
                max_retries=1,
            ),
            PlanStep(
                step_id=2,
                title="Produce the main deliverable",
                owner="coder",
                instruction=(
                    f"Create the main deliverable for: {query}. "
                    f"It must be detailed, implementation-oriented, and satisfy the clarified success criteria."
                ),
                depends_on=[1],
                can_run_parallel=True,
                fallback_owners=["researcher"],
                required_tools=["file_agent"] if wants_file else [],
                expected_output="main deliverable",
                success_checks=[
                    "main deliverable produced",
                    "artifact saved if requested" if wants_file else "usable output produced",
                    "goes beyond shallow summary",
                ],
                max_retries=2,
            ),
            PlanStep(
                step_id=3,
                title="Analyze completeness and practicality",
                owner="analyst",
                instruction=(
                    f"Analyze the deliverable for completeness, depth, tradeoffs, usability, gaps, "
                    f"and practical execution quality for: {query}"
                ),
                depends_on=[1],
                can_run_parallel=True,
                fallback_owners=["researcher"],
                expected_output="quality analysis",
                success_checks=[
                    "gaps identified",
                    "practicality reviewed",
                    "tradeoffs reviewed",
                ],
                max_retries=1,
            ),
        ]

    def _build_deterministic_plan(self, query: str) -> PlanResult:
        task_type = detect_task_type(query)
        target_file = choose_target_file_from_query(query)
        output_path = choose_output_path_from_query(query)

        steps = self._build_generic_plan(query, task_type, output_path)

        return PlanResult(
            steps=steps,
            planning_notes="Generic planner-worker-validator graph derived from task contract, not from domain-specific routing.",
            task_type=task_type,
            target_file=target_file,
            output_path=output_path,
        )

    @message_handler
    async def handle_task(self, message: NexusTask, ctx: MessageContext) -> PlanResult:
        self._logger.add("planner", "start", {"query": message.query})

        result = self._build_deterministic_plan(message.query)

        self._logger.add(
            "planner",
            "finish",
            {
                "task_type": result.task_type,
                "target_file": result.target_file,
                "output_path": result.output_path,
                "steps": [asdict(step) for step in result.steps],
            },
        )
        return result