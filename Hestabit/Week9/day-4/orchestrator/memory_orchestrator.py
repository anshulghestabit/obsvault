from __future__ import annotations

import asyncio
import os
import uuid

from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from memory.session_memory import SessionMemory
from memory.sqlite_store import SQLiteStore
from memory.vector_store import FaissSQLiteMemory


ANSWER_SYSTEM_PROMPT = """
You are a memory-aware local AI assistant running on LM Studio.

Rules:
1. Use the current user query first.
2. Use recent session context when useful.
3. Use retrieved long-term memory only when relevant.
4. Never invent memories that were not retrieved or provided in the current session.
5. If retrieved memory conflicts with the user's latest message, prefer the latest user message.
6. Be concise, direct, and helpful.
""".strip()


FACT_EXTRACTOR_SYSTEM_PROMPT = """
You extract durable, memory-worthy facts from a single user/assistant exchange.

Keep only stable items worth remembering later, such as:
- preferences
- constraints
- project goals
- ongoing tasks
- personal work context
- durable decisions

Do NOT store:
- temporary greetings
- filler language
- obvious restatements
- one-off conversational fluff

Return only bullet points in exactly this format:
- fact text | category=semantic

Allowed categories:
semantic, preference, constraint, project, episodic
""".strip()


class MemoryOrchestrator:
    def __init__(self) -> None:
        load_dotenv()

        base_url = os.environ["LM_STUDIO_BASE_URL"]
        api_key = os.environ.get("LM_STUDIO_API_KEY", "lm-studio")
        chat_model = os.environ["LM_STUDIO_CHAT_MODEL"]
        embed_model = os.environ["LM_STUDIO_EMBED_MODEL"]

        session_window_size = int(os.environ.get("SESSION_WINDOW_SIZE", "10"))
        top_k = int(os.environ.get("VECTOR_TOP_K", "4"))
        score_threshold = float(os.environ.get("VECTOR_SCORE_THRESHOLD", "0.35"))

        sqlite_db_path = os.environ.get("SQLITE_DB_PATH", "memory/long_term.db")
        faiss_index_path = os.environ.get("FAISS_INDEX_PATH", "memory/faiss.index")
        faiss_meta_path = os.environ.get("FAISS_META_PATH", "memory/faiss_meta.json")

        self.session_memory = SessionMemory(window_size=session_window_size)
        self.sqlite_store = SQLiteStore(db_path=sqlite_db_path)
        self.long_term_memory = FaissSQLiteMemory(
            sqlite_store=self.sqlite_store,
            base_url=base_url,
            api_key=api_key,
            embed_model=embed_model,
            faiss_index_path=faiss_index_path,
            faiss_meta_path=faiss_meta_path,
            k=top_k,
            score_threshold=score_threshold,
        )

        model_info = {
            "vision": False,
            "function_calling": True,
            "json_output": False,
            "structured_output": False,
            "family": "qwen",
            "multiple_system_messages": True,
        }

        self.answer_model_client = OpenAIChatCompletionClient(
            model=chat_model,
            base_url=base_url,
            api_key=api_key,
            model_info=model_info,
        )

        self.fact_model_client = OpenAIChatCompletionClient(
            model=chat_model,
            base_url=base_url,
            api_key=api_key,
            model_info=model_info,
        )

        self.answer_agent = AssistantAgent(
            name="memory_answer_agent",
            system_message=ANSWER_SYSTEM_PROMPT,
            model_client=self.answer_model_client,
            memory=[self.long_term_memory],
        )

        self.fact_extractor_agent = AssistantAgent(
            name="memory_fact_extractor",
            system_message=FACT_EXTRACTOR_SYSTEM_PROMPT,
            model_client=self.fact_model_client,
        )

    def _build_task(self, user_query: str) -> str:
        session_context = self.session_memory.render_for_prompt()
        return f"""
Recent short-term session context:
{session_context}

Current user query:
{user_query}

Answer the current query naturally.
Use relevant memory only when it genuinely helps.
""".strip()

    @staticmethod
    def _extract_final_text(task_result: object) -> str:
        messages = getattr(task_result, "messages", [])
        for message in reversed(messages):
            content = getattr(message, "content", None)
            if isinstance(content, str) and content.strip():
                return content.strip()
        return "I could not generate a valid response."

    @staticmethod
    def _parse_fact_lines(text: str) -> list[tuple[str, str]]:
        facts: list[tuple[str, str]] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue

            body = stripped[2:].strip()
            if not body:
                continue

            if "| category=" in body:
                fact_text, category = body.rsplit("| category=", 1)
                fact_text = fact_text.strip()
                category = category.strip().lower()
            else:
                fact_text = body
                category = "semantic"

            if fact_text:
                facts.append((fact_text, category))

        # keep memory tight
        return facts[:5]

    async def _store_exchange(self, turn_id: str, user_query: str, answer: str) -> None:
        await self.long_term_memory.remember_conversation(
            role="user",
            content=user_query,
            metadata={"source_turn_id": turn_id, "kind": "conversation"},
        )
        await self.long_term_memory.remember_conversation(
            role="assistant",
            content=answer,
            metadata={"source_turn_id": turn_id, "kind": "conversation"},
        )

    async def _extract_and_store_facts(self, turn_id: str, user_query: str, answer: str) -> None:
        extraction_prompt = f"""
Interaction to analyze:

USER:
{user_query}

ASSISTANT:
{answer}

Extract only durable facts worth saving for future recall.
Return only bullet points in the required format.
If nothing is worth storing, return an empty response.
""".strip()

        result = await self.fact_extractor_agent.run(task=extraction_prompt)
        raw_text = self._extract_final_text(result)
        facts = self._parse_fact_lines(raw_text)

        for fact_text, category in facts:
            await self.long_term_memory.remember_fact(
                content=fact_text,
                category=category,
                source_turn_id=turn_id,
                metadata={"kind": "fact", "source": "fact_extractor"},
            )

    async def ask(self, user_query: str) -> str:
        turn_id = str(uuid.uuid4())

        self.session_memory.add_user(user_query)

        result = await self.answer_agent.run(task=self._build_task(user_query))
        answer = self._extract_final_text(result)

        self.session_memory.add_assistant(answer)

        await self._store_exchange(turn_id=turn_id, user_query=user_query, answer=answer)
        await self._extract_and_store_facts(turn_id=turn_id, user_query=user_query, answer=answer)

        return answer

    async def print_recent_facts(self, limit: int = 10) -> None:
        rows = self.sqlite_store.get_recent_facts(limit=limit)
        if not rows:
            print("No stored facts found.")
            return

        print("\nRecent facts:")
        for row in rows:
            print(f"- [{row.category}] {row.content}")

    async def close(self) -> None:
        await self.answer_model_client.close()
        await self.fact_model_client.close()
        await self.long_term_memory.close()


async def interactive_cli() -> None:
    orchestrator = MemoryOrchestrator()

    print("\nDay 4 Memory Orchestrator is ready.")
    print("Commands:")
    print("  /session  -> show short-term session memory")
    print("  /facts    -> show recent long-term facts")
    print("  /exit     -> quit\n")

    try:
        while True:
            user_query = (await asyncio.to_thread(input, "You: ")).strip()

            if not user_query:
                continue

            lowered = user_query.lower()

            if lowered in {"/exit", "exit", "quit"}:
                break

            if lowered == "/session":
                print("\nShort-term session memory:")
                print(orchestrator.session_memory.render_for_prompt())
                print()
                continue

            if lowered == "/facts":
                await orchestrator.print_recent_facts(limit=10)
                print()
                continue

            try:
                answer = await orchestrator.ask(user_query)
                print(f"\nAssistant: {answer}\n")
            except Exception as e:
                print(f"\nError while processing request: {e}\n")

    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(interactive_cli())