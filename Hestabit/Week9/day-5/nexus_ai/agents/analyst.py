from __future__ import annotations

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.models import WorkerInput, WorkerOutput


class AnalystAgent(NexusBaseAgent):
    @message_handler
    async def handle_input(self, message: WorkerInput, ctx: MessageContext) -> WorkerOutput:
        self._logger.add(
            "analyst",
            "start",
            {
                "step_id": message.step.step_id,
                "title": message.step.title,
                "task_type": message.task_type,
                "target_file": message.target_file,
            },
        )

        system_prompt = (
            "You are the Analyst in NEXUS AI. "
            "Focus on tradeoffs, business impact, feasibility, prioritization, risk, and decision quality. "
            "If the query involves a dataset, convert grounded findings into actions, strategy, and implications. "
            "Do not write code."
        )

        user_prompt = (
            f"Original query:\n{message.original_query}\n\n"
            f"Task type:\n{message.task_type}\n\n"
            f"Memory context:\n{message.memory_context}\n\n"
            f"Target file:\n{message.target_file}\n\n"
            f"Assigned step:\n{message.step.instruction}"
        )

        text = await self._llm_text(system_prompt, user_prompt)

        result = WorkerOutput(
            step_id=message.step.step_id,
            owner="analyst",
            title=message.step.title,
            result=text,
            artifacts={
                "execution_passed": True,
            },
        )

        self._logger.add(
            "analyst",
            "finish",
            {
                "step_id": message.step.step_id,
                "result_preview": text[:500],
            },
        )
        return result