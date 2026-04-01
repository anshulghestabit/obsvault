from __future__ import annotations

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.models import WorkerInput, WorkerOutput
from tools.db_agent import csv_columns, csv_schema, preview_csv


class ResearcherAgent(NexusBaseAgent):
    @message_handler
    async def handle_input(self, message: WorkerInput, ctx: MessageContext) -> WorkerOutput:
        self._logger.add(
            "researcher",
            "start",
            {
                "step_id": message.step.step_id,
                "title": message.step.title,
                "task_type": message.task_type,
                "target_file": message.target_file,
            },
        )

        file_context = ""
        if message.target_file:
            if message.target_file.lower().endswith(".csv"):
                file_context = (
                    f"Target file: {message.target_file}\n"
                    f"Columns: {csv_columns(message.target_file)}\n\n"
                    f"Schema: {csv_schema(message.target_file)}\n\n"
                    f"Preview: {preview_csv(message.target_file, limit=5)}"
                )
            else:
                file_context = f"Target file: {message.target_file}"

        system_prompt = (
            "You are the Researcher in NEXUS AI. "
            "Provide concise factual, domain, strategic, or requirements context for the assigned step. "
            "Use the file context when available. "
            "Do not write code and do not produce the final answer."
        )

        user_prompt = (
            f"Original query:\n{message.original_query}\n\n"
            f"Task type:\n{message.task_type}\n\n"
            f"Memory context:\n{message.memory_context}\n\n"
            f"File context:\n{file_context}\n\n"
            f"Assigned step:\n{message.step.instruction}"
        )

        text = await self._llm_text(system_prompt, user_prompt)

        result = WorkerOutput(
            step_id=message.step.step_id,
            owner="researcher",
            title=message.step.title,
            result=text,
            artifacts={
                "grounded_file": message.target_file,
                "execution_passed": True,
            },
        )

        self._logger.add(
            "researcher",
            "finish",
            {
                "step_id": message.step.step_id,
                "result_preview": text[:500],
            },
        )
        return result