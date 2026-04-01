"""
Day 3 — Tool-Calling Agents (Code, Files, Database)
Architecture: Orchestrator → File Agent + DB Agent + Code Agent → Report Agent
All agents use registered tools. DB is initialised by the DB Agent itself.
"""
import asyncio
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.model_context import BufferedChatCompletionContext
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Stop tokens tell the model to halt the moment it writes the terminator word.
# Without these, local models keep generating past the terminator into garbage /
# foreign-language tokens because they have no signal that they are done.
_FILE_STOP  = ["FILE_AGENT_DONE"]
_DB_STOP    = ["DB_AGENT_DONE"]
_CODE_STOP  = ["CODE_AGENT_DONE"]
_REPORT_STOP = ["TERMINATE"]

from tools.file_agent import (
    read_text_file,
    write_text_file,
    read_csv_preview,
    list_files_in_directory,
)
from tools.db_agent import (
    load_csv_into_sqlite,
    run_sql_query,
    describe_table,
)
from tools.code_executor import (
    analyze_sales_csv,
    compute_top_n_products,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_status(message: str) -> None:
    print(f"[INFO] {message}")


# ---------------------------------------------------------------------------
# Model client
# ---------------------------------------------------------------------------

def build_model_client(stop: list[str] | None = None) -> OpenAIChatCompletionClient:
    return OpenAIChatCompletionClient(
        model=get_required_env("MODEL_NAME"),
        base_url=get_required_env("BASE_URL"),
        api_key=os.getenv("API_KEY", "lm-studio"),
        temperature=float(os.getenv("TEMPERATURE", "0.05")),
        max_tokens=int(os.getenv("MAX_TOKENS", "512")),
        parallel_tool_calls=False,
        # stop sequences: model halts the instant it emits the terminator token,
        # preventing the drift / foreign-language repetition seen in local models.
        extra_create_args={"stop": stop} if stop else {},
        model_info=ModelInfo(
            vision=False,
            function_calling=True,
            json_output=False,
            family="unknown",
            structured_output=False,
        ),
    )


# ---------------------------------------------------------------------------
# Agent builders
# ---------------------------------------------------------------------------

def build_file_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """
    Handles file inspection: listing directories, reading text/CSV files,
    writing output files.
    reflect_on_tool_use=False — the tool output IS the answer; reflection
    only adds tokens that drift into garbage on local models.
    """
    return AssistantAgent(
        name="file_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=6),
        tools=[
            list_files_in_directory,
            read_text_file,
            write_text_file,
            read_csv_preview,
        ],
        reflect_on_tool_use=False,
        system_message=(
            "You are the File Agent. Call read_csv_preview on the given path.\n"
            "Then reply with ONLY these three lines and nothing else:\n"
            "ROWS: <number>\n"
            "COLUMNS: <list>\n"
            "SUMMARY: <one sentence>\n"
            "FILE_AGENT_DONE"
        ),
    )


def build_db_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """
    Handles SQLite queries.
    reflect_on_tool_use=False — after run_sql_query returns rows, local models
    that 'reflect' tend to fill the extra generation budget with repetition or
    foreign-language tokens. We take the tool result directly and format it in
    the system prompt instead.
    """
    return AssistantAgent(
        name="db_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=6),
        tools=[
            load_csv_into_sqlite,
            describe_table,
            run_sql_query,
        ],
        reflect_on_tool_use=False,
        system_message=(
            "You are the DB Agent. The database is ready; the table is named 'sales'.\n"
            "Call run_sql_query with the exact SQL given to you.\n"
            "After the tool returns, write ONLY:\n"
            "RESULT: <one or two sentences stating the top and bottom region by revenue>\n"
            "DB_AGENT_DONE\n"
            "Do not write anything else. Do not repeat the query. Do not add commentary."
        ),
    )


def build_code_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """
    Handles Python-based analysis: business insights and top-product rankings.
    reflect_on_tool_use=False — both tools return structured text that is
    already human-readable. Reflection doubles token generation and is the
    second most common place local models start drifting.
    """
    return AssistantAgent(
        name="code_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=6),
        tools=[
            analyze_sales_csv,
            compute_top_n_products,
        ],
        reflect_on_tool_use=False,
        system_message=(
            "You are the Code Agent.\n"
            "Step 1: call analyze_sales_csv with the given CSV path.\n"
            "Step 2: call compute_top_n_products with the same path and n=5.\n"
            "After both tools return, copy their output verbatim, then write:\n"
            "CODE_AGENT_DONE\n"
            "Do not add any other text, explanation, or commentary."
        ),
    )


def build_report_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """
    Synthesises outputs from File, DB, and Code agents into a final user-facing report.
    No tools — reasoning only.
    """
    return AssistantAgent(
        name="report_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=6),
        system_message=(
            "You are the Report Agent. Write a final report with exactly these sections:\n"
            "## Dataset Overview\n"
            "<2 sentences>\n\n"
            "## Top 5 Business Insights\n"
            "1. ...\n2. ...\n3. ...\n4. ...\n5. ...\n\n"
            "## Recommended Next Action\n"
            "<1 sentence>\n\n"
            "TERMINATE\n\n"
            "Use only the data given to you. Do not add any text after TERMINATE."
        ),
    )


# ---------------------------------------------------------------------------
# Agent runner
# ---------------------------------------------------------------------------

async def ask_agent(
    agent: AssistantAgent,
    source: str,
    prompt: str,
    timeout_seconds: int,
) -> str:
    print(f"\n[STARTED]  {agent.name}")
    try:
        response = await asyncio.wait_for(
            agent.on_messages(
                [TextMessage(content=prompt, source=source)],
                CancellationToken(),
            ),
            timeout=timeout_seconds,
        )
        content = response.chat_message.content
        print(f"[FINISHED] {agent.name}")
        return content
    except asyncio.TimeoutError:
        msg = f"ERROR: {agent.name} timed out after {timeout_seconds}s."
        print(f"[TIMEOUT]  {agent.name}")
        return msg
    except Exception as exc:
        msg = f"ERROR: {agent.name} raised an exception: {exc}"
        print(f"[ERROR]    {agent.name}: {exc}")
        return msg


# ---------------------------------------------------------------------------
# Main orchestration flow
# ---------------------------------------------------------------------------

async def run_day3_flow(user_query: str) -> None:
    timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "120"))

    # Each agent gets its own client with the stop token that matches its
    # terminator word. The LM Studio / OpenAI-compatible backend will halt
    # generation the instant it emits that token — no more runaway output.
    file_agent   = build_file_agent(build_model_client(_FILE_STOP))
    db_agent     = build_db_agent(build_model_client(_DB_STOP))
    code_agent   = build_code_agent(build_model_client(_CODE_STOP))
    report_agent = build_report_agent(build_model_client(_REPORT_STOP))

    csv_path = os.path.abspath("data/100 Sales Records.csv")
    print_status(f"CSV path: {csv_path}")

    # ------------------------------------------------------------------
    # Pre-load: initialise SQLite DB before agents run so db_agent only
    # needs to query, not set up. This mirrors the Day-3 requirement that
    # the orchestrator handles setup and agents handle their specialist job.
    # ------------------------------------------------------------------
    print_status("Pre-loading CSV into SQLite …")
    preload_result = load_csv_into_sqlite(csv_path, "sales")
    print_status(preload_result)

    schema = describe_table("sales")
    print_status("Schema:\n" + schema)

    # ------------------------------------------------------------------
    # Step 1 — File Agent: inspect the CSV
    # ------------------------------------------------------------------
    file_prompt = (
        f"Preview the CSV file at this path: {csv_path}\n"
        "Call read_csv_preview to inspect it.\n"
        "Report the row count, column names, and a one-sentence description of what the data contains."
    )
    file_output = await ask_agent(file_agent, "orchestrator", file_prompt, timeout_seconds)

    # ------------------------------------------------------------------
    # Step 2 — DB Agent: run revenue-by-region SQL query
    # ------------------------------------------------------------------
    db_prompt = (
        "The SQLite database is ready. The table is named 'sales'.\n"
        "Run exactly this SQL query using run_sql_query:\n\n"
        "SELECT region, SUM(units * unit_price) AS total_revenue "
        "FROM sales "
        "GROUP BY region "
        "ORDER BY total_revenue DESC;\n\n"
        "Summarise which region earned the most and the least revenue."
    )
    db_output = await ask_agent(db_agent, "orchestrator", db_prompt, timeout_seconds)

    # ------------------------------------------------------------------
    # Step 3 — Code Agent: Python analysis
    # ------------------------------------------------------------------
    code_prompt = (
        f"Analyse the sales data at: {csv_path}\n"
        "First call analyze_sales_csv to get all business insights.\n"
        f"Then call compute_top_n_products with n=5 to get the top 5 products by revenue.\n"
        "Report all findings."
    )
    code_output = await ask_agent(code_agent, "orchestrator", code_prompt, timeout_seconds)

    # ------------------------------------------------------------------
    # Step 4 — Report Agent: synthesise everything
    # ------------------------------------------------------------------
    report_prompt = (
        f"USER QUERY:\n{user_query}\n\n"
        f"FILE AGENT OUTPUT:\n{file_output}\n\n"
        f"DB AGENT OUTPUT:\n{db_output}\n\n"
        f"CODE AGENT OUTPUT:\n{code_output}\n\n"
        "Now generate the final user-facing report."
    )
    final_output = await ask_agent(report_agent, "orchestrator", report_prompt, timeout_seconds)

    # ------------------------------------------------------------------
    # Print all outputs
    # ------------------------------------------------------------------
    print_section("FILE AGENT OUTPUT")
    print(file_output)

    print_section("DB AGENT OUTPUT")
    print(db_output)

    print_section("CODE AGENT OUTPUT")
    print(code_output)

    print_section("FINAL REPORT")
    print(final_output)

    for agent in (file_agent, db_agent, code_agent, report_agent):
        await agent.model_client.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    query = input("Enter your query: ").strip()
    if not query:
        query = "Analyse sales.csv and generate top 5 insights."
    asyncio.run(run_day3_flow(query))
