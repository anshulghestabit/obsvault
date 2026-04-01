from __future__ import annotations

import json
from dataclasses import asdict

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.models import CritiqueInput, CritiqueResult


class CriticAgent(NexusBaseAgent):
    @message_handler
    async def handle_input(self, message: CritiqueInput, ctx: MessageContext) -> CritiqueResult:
        self._logger.add(
            "critic",
            "start",
            {
                "task_type": message.task_type,
                "worker_outputs": len(message.worker_outputs),
            },
        )

        system_prompt = (
            "You are the Critic in NEXUS AI. "
            "Find weak reasoning, missing steps, risky assumptions, execution failures, and grounding gaps. "
            "Return JSON only: {\"critique\":\"...\",\"risks\":[\"...\", ...]}"
        )
        user_prompt = (
            f"Query:\n{message.query}\n\n"
            f"Task type:\n{message.task_type}\n\n"
            f"Plan:\n{json.dumps([asdict(s) for s in message.plan], indent=2)}\n\n"
            f"Worker outputs:\n{json.dumps([asdict(o) for o in message.worker_outputs], indent=2)}"
        )

        raw = await self._llm_text(system_prompt, user_prompt)

        try:
            data = json.loads(raw)
            result = CritiqueResult(
                critique=data.get("critique", ""),
                risks=data.get("risks", []),
            )
        except Exception:
            risks = []
            for output in message.worker_outputs:
                if output.artifacts.get("execution_passed") is False:
                    risks.append(f"{output.owner} step {output.step_id} had execution failure.")
            if not risks:
                risks.append("Possible missing details or weak grounding.")
            result = CritiqueResult(
                critique="Fallback critique: review grounding, completeness, and execution truth.",
                risks=risks,
            )

        self._logger.add(
            "critic",
            "finish",
            {
                "critique_preview": result.critique[:400],
                "risks": result.risks,
            },
        )
        return result