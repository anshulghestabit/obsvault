from __future__ import annotations

from dataclasses import asdict

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.models import OptimizationInput, OptimizationResult


class OptimizerAgent(NexusBaseAgent):
    @message_handler
    async def handle_input(self, message: OptimizationInput, ctx: MessageContext) -> OptimizationResult:
        self._logger.add(
            "optimizer",
            "start",
            {
                "task_type": message.task_type,
                "worker_outputs": len(message.worker_outputs),
            },
        )

        if any(o.artifacts.get("mode") == "code_generation" for o in message.worker_outputs):
            coder = next((o for o in message.worker_outputs if o.owner == "coder"), None)
            improved = coder.result if coder else "\n\n".join(o.result for o in message.worker_outputs)
            result = OptimizationResult(
                improved_draft=improved,
                improvements=["Preserved execution-validated implementation output."],
            )
        else:
            system_prompt = (
                "You are the Optimizer in NEXUS AI. "
                "Rewrite the worker outputs into a deeper, cleaner, more complete final draft. "
                "Do not just concatenate. "
                "Use the critique to close gaps, improve structure, increase depth, and produce a more implementation-ready answer. "
                "Return JSON only with keys: improved_draft, improvements."
            )
            user_prompt = (
                f"Query:\n{message.query}\n\n"
                f"Task type:\n{message.task_type}\n\n"
                f"Worker outputs:\n{[asdict(o) for o in message.worker_outputs]}\n\n"
                f"Critique:\n{message.critique}"
            )

            data = await self._llm_json(system_prompt, user_prompt)
            improved_draft = str(data.get("improved_draft", "")).strip()
            improvements = list(data.get("improvements", []))

            if not improved_draft:
                merged = ["# Synthesized Response", ""]
                for output in message.worker_outputs:
                    merged.append(f"## {output.owner.capitalize()} — {output.title}")
                    merged.append(output.result.strip())
                    merged.append("")
                if message.critique:
                    merged.append("## Critique To Address")
                    merged.append(message.critique.strip())
                improved_draft = "\n".join(merged).strip()
                improvements = improvements or ["Used structured synthesis fallback instead of raw concatenation."]

            result = OptimizationResult(
                improved_draft=improved_draft,
                improvements=improvements,
            )

        self._logger.add(
            "optimizer",
            "finish",
            {
                "draft_preview": result.improved_draft[:600],
                "improvements": result.improvements,
            },
        )
        return result