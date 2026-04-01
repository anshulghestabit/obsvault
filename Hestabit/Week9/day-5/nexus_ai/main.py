from __future__ import annotations

import asyncio
import logging

from autogen_core import AgentId, SingleThreadedAgentRuntime

from memory.session_memory import SessionMemory
from memory.vector_store import FaissVectorStore
from nexus_ai.agents.analyst import AnalystAgent
from nexus_ai.agents.coder import CoderAgent
from nexus_ai.agents.completion_checker import CompletionCheckerAgent
from nexus_ai.agents.critic import CriticAgent
from nexus_ai.agents.optimizer import OptimizerAgent
from nexus_ai.agents.orchestrator import OrchestratorAgent
from nexus_ai.agents.planner import PlannerAgent
from nexus_ai.agents.reporter import ReporterAgent
from nexus_ai.agents.researcher import ResearcherAgent
from nexus_ai.agents.toolsmith import ToolsmithAgent
from nexus_ai.agents.validator import ValidatorAgent
from nexus_ai.config import get_nexus_settings
from nexus_ai.logger import NexusLogger
from nexus_ai.models import NexusTask
from utils.llm_factory import build_text_model_client


async def main() -> None:
    settings = get_nexus_settings()

    if settings.debug_mode:
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger("autogen_core").setLevel(logging.DEBUG)

    model_client = build_text_model_client(settings)
    nexus_logger = NexusLogger(settings.log_dir, debug_mode=settings.debug_mode)
    session_memory = SessionMemory(db_path=settings.session_db_path, max_turns=10)
    vector_store = FaissVectorStore(
        index_path=settings.vector_index_path,
        metadata_path=settings.vector_metadata_path,
        dim=1024,
    )

    runtime = SingleThreadedAgentRuntime()

    await PlannerAgent.register(runtime, "planner", lambda: PlannerAgent("planner", model_client, nexus_logger, settings.debug_mode))
    await ResearcherAgent.register(runtime, "researcher", lambda: ResearcherAgent("researcher", model_client, nexus_logger, settings.debug_mode))
    await CoderAgent.register(runtime, "coder", lambda: CoderAgent("coder", model_client, nexus_logger, settings.debug_mode))
    await AnalystAgent.register(runtime, "analyst", lambda: AnalystAgent("analyst", model_client, nexus_logger, settings.debug_mode))
    await CriticAgent.register(runtime, "critic", lambda: CriticAgent("critic", model_client, nexus_logger, settings.debug_mode))
    await OptimizerAgent.register(runtime, "optimizer", lambda: OptimizerAgent("optimizer", model_client, nexus_logger, settings.debug_mode))
    await CompletionCheckerAgent.register(
        runtime,
        "completion_checker",
        lambda: CompletionCheckerAgent("completion_checker", model_client, nexus_logger, settings.debug_mode),
    )
    await ToolsmithAgent.register(
        runtime,
        "toolsmith",
        lambda: ToolsmithAgent("toolsmith", model_client, nexus_logger, settings.debug_mode),
    )
    await ValidatorAgent.register(runtime, "validator", lambda: ValidatorAgent("validator", model_client, nexus_logger, settings.debug_mode))
    await ReporterAgent.register(runtime, "reporter", lambda: ReporterAgent("reporter", model_client, nexus_logger, settings.debug_mode))
    await OrchestratorAgent.register(
        runtime,
        "orchestrator",
        lambda: OrchestratorAgent(
            "orchestrator",
            model_client,
            nexus_logger,
            session_memory,
            vector_store,
            settings.debug_mode,
        ),
    )

    runtime.start()

    try:
        user_query = input("\nEnter your NEXUS AI task: ").strip()
        if not user_query:
            print("No task entered. Exiting.")
            return

        result = await runtime.send_message(
            NexusTask(query=user_query),
            AgentId("orchestrator", "default"),
        )

        print("\n" + "=" * 80)
        print("NEXUS AI FINAL ANSWER")
        print("=" * 80)
        print(result.final_answer)

        print("\n" + "=" * 80)
        print("EXECUTION TREE")
        print("=" * 80)
        print(result.execution_tree)

        print("\n" + "=" * 80)
        print("VALIDATION ISSUES")
        print("=" * 80)
        if result.validation_issues:
            for issue in result.validation_issues:
                print(f"- {issue}")
        else:
            print("No issues reported.")

        print("\n" + "=" * 80)
        print("LOG FILE")
        print("=" * 80)
        print(result.log_path)
    finally:
        await runtime.stop_when_idle()
        if hasattr(model_client, "close"):
            await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())