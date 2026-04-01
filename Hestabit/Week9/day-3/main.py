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

def build_model_client() -> OpenAIChatCompletionClient:
    return OpenAIChatCompletionClient(
        model=get_required_env("MODEL_NAME"),
        base_url=get_required_env("BASE_URL"),
        api_key=os.getenv("API_KEY", "lm-studio"),
        temperature=float(os.getenv("TEMPERATURE", "0.05")),
        max_tokens=int(os.getenv("MAX_TOKENS", "512")),
        parallel_tool_calls=False,
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
    """
    return AssistantAgent(
        name="file_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=10),
        tools=[
            list_files_in_directory,
            read_text_file,
            write_text_file,
            read_csv_preview,
        ],
        reflect_on_tool_use=True,
        system_message=(
            "You are the File Agent.\n"
            "Your only job is to inspect files and preview CSV/text data using your tools.\n"
            "Always call read_csv_preview to inspect the CSV before responding.\n"
            "Report: file path, row count, column names, and a brief data description.\n"
            "Do not perform any analysis or SQL queries.\n"
            "Keep your response under 120 words.\n"
            "End your response with FILE_AGENT_DONE."
        ),
    )


def build_db_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """
    Handles all SQLite operations: loading CSV data, describing schema,
    and running SELECT queries.
    """
    return AssistantAgent(
        name="db_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=10),
        tools=[
            load_csv_into_sqlite,   # registered so agent can call it if needed
            describe_table,         # registered so agent can inspect schema
            run_sql_query,
        ],
        reflect_on_tool_use=True,
        system_message=(
            "You are the DB Agent.\n"
            "The SQLite database has already been initialised with a table named 'sales'.\n"
            "Your job is to call run_sql_query with the SQL you are given, then summarise the result.\n"
            "Do not ask for file paths. Do not load data yourself unless explicitly told to.\n"
            "After the tool returns, report the result clearly in under 100 words.\n"
            "End your response with DB_AGENT_DONE."
        ),
    )


def build_code_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """
    Handles Python-based analysis: business insights and top-product rankings.
    """
    return AssistantAgent(
        name="code_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=10),
        tools=[
            analyze_sales_csv,
            compute_top_n_products,
        ],
        reflect_on_tool_use=True,
        system_message=(
            "You are the Code Agent.\n"
            "Use your Python analysis tools on the CSV path provided.\n"
            "Call analyze_sales_csv first, then compute_top_n_products.\n"
            "Return all insights produced by the tools — do not omit any numbered point.\n"
            "Keep your response under 150 words.\n"
            "End your response with CODE_AGENT_DONE."
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
        model_context=BufferedChatCompletionContext(buffer_size=10),
        system_message=(
            "You are the Report Agent.\n"
            "You receive structured outputs from the File Agent, DB Agent, and Code Agent.\n"
            "Synthesise them into a clear final report with exactly these sections:\n"
            "1. Dataset Overview — brief description of the data\n"
            "2. Top 5 Business Insights — numbered list drawn from all agent outputs\n"
            "3. Recommended Next Action — one concrete, actionable step\n"
            "Keep the total response under 250 words.\n"
            "End your response with TERMINATE."
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
    model_client = build_model_client()

    # Build all agents sharing the same model client
    file_agent = build_file_agent(model_client)
    db_agent   = build_db_agent(model_client)
    code_agent = build_code_agent(model_client)
    report_agent = build_report_agent(model_client)

    csv_path = os.path.abspath("data/sales.csv")
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

    await model_client.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    query = input("Enter your query: ").strip()
    if not query:
        query = "Analyse sales.csv and generate top 5 insights."
    asyncio.run(run_day3_flow(query))
