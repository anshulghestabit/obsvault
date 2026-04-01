# Python Project Dump

## Folder Structure
```
.
├── data
│   └── sales.csv
├── .env
├── files
├── main_2ndpass.py
├── main.py
├── outputs
│   └── day3.db
├── python_project_dump.md
├── requirements.txt
├── TOOL-CHAIN.md
└── tools
    ├── code_executor.py
    ├── db_agent.py
    ├── file_agent.py
    └── __init__.py

5 directories, 12 files
```

## FILE: ./main_2ndpass.py

```py
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

```

## FILE: ./main.py

```py
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

```

## FILE: ./requirements.txt

```txt
autogen-agentchat
autogen-ext[openai]
pandas

```

## FILE: ./tools/code_executor.py

```py
from pathlib import Path
import pandas as pd


def analyze_sales_csv(csv_path: str) -> str:
    """
    Analyze a sales CSV file and return key business insights using Python + pandas.
    Required columns: date, region, product, units, unit_price.
    """
    path = Path(csv_path)
    if not path.exists():
        return f"ERROR: CSV not found: {csv_path}"
    try:
        df = pd.read_csv(path)
        required = {"date", "region", "product", "units", "unit_price"}
        missing = required - set(df.columns)
        if missing:
            return f"ERROR: Missing required columns: {sorted(missing)}"

        df["revenue"] = df["units"] * df["unit_price"]

        total_revenue = float(df["revenue"].sum())
        total_units = int(df["units"].sum())

        top_product = (
            df.groupby("product", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=False)
            .iloc[0]
        )

        top_region = (
            df.groupby("region", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=False)
            .iloc[0]
        )

        avg_order_value = float(df["revenue"].mean())

        highest_units_product = (
            df.groupby("product", as_index=False)["units"]
            .sum()
            .sort_values("units", ascending=False)
            .iloc[0]
        )

        lowest_revenue_region = (
            df.groupby("region", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=True)
            .iloc[0]
        )

        insights = [
            f"1. Total revenue: {total_revenue:.2f}.",
            f"2. Total units sold: {total_units}.",
            f"3. Top revenue product: {top_product['product']} "
            f"({float(top_product['revenue']):.2f}).",
            f"4. Top revenue region: {top_region['region']} "
            f"({float(top_region['revenue']):.2f}).",
            f"5. Highest volume product: {highest_units_product['product']} "
            f"({int(highest_units_product['units'])} units).",
            f"6. Average transaction revenue: {avg_order_value:.2f}.",
            f"7. Lowest revenue region: {lowest_revenue_region['region']} "
            f"({float(lowest_revenue_region['revenue']):.2f}) — needs attention.",
        ]
        return "\n".join(insights)
    except Exception as exc:
        return f"ERROR: Python analysis failed: {exc}"


def compute_top_n_products(csv_path: str, n: int = 5) -> str:
    """
    Return the top N products by total revenue from a sales CSV file.
    Defaults to top 5.
    """
    path = Path(csv_path)
    if not path.exists():
        return f"ERROR: CSV not found: {csv_path}"
    try:
        df = pd.read_csv(path)
        df["revenue"] = df["units"] * df["unit_price"]
        result = (
            df.groupby("product", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=False)
            .head(n)
        )
        return f"TOP_{n}_PRODUCTS_BY_REVENUE:\n{result.to_string(index=False)}"
    except Exception as exc:
        return f"ERROR: Could not compute top products: {exc}"


```

## FILE: ./tools/db_agent.py

```py
import sqlite3
from pathlib import Path
import pandas as pd


DB_PATH = "outputs/day3.db"


def load_csv_into_sqlite(csv_path: str, table_name: str = "sales") -> str:
    """
    Load a CSV file into a SQLite database table, replacing it if it already exists.
    Always call this before running any SQL queries.
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        return f"ERROR: CSV not found: {csv_path}"
    try:
        Path("outputs").mkdir(parents=True, exist_ok=True)
        df = pd.read_csv(csv_file)
        conn = sqlite3.connect(DB_PATH)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()
        return (
            f"SUCCESS: Loaded {len(df)} rows from {csv_path} "
            f"into SQLite table '{table_name}' at {DB_PATH}"
        )
    except Exception as exc:
        return f"ERROR: Failed to load CSV into SQLite: {exc}"


def run_sql_query(query: str) -> str:
    """
    Run a read-only SELECT query against the local SQLite database and return results as text.
    The database is at outputs/day3.db and contains a table named 'sales'.
    """
    db_file = Path(DB_PATH)
    if not db_file.exists():
        return (
            "ERROR: Database not found. "
            "Call load_csv_into_sqlite first to initialise it."
        )
    try:
        conn = sqlite3.connect(DB_PATH)
        query_clean = query.strip().lower()
        if not query_clean.startswith("select"):
            conn.close()
            return "ERROR: Only SELECT queries are allowed."
        df = pd.read_sql_query(query, conn)
        conn.close()
        if df.empty:
            return "QUERY_RESULT: No rows returned."
        return (
            f"QUERY_RESULT_ROWS: {len(df)}\n"
            f"COLUMNS: {list(df.columns)}\n"
            f"DATA:\n{df.to_string(index=False)}"
        )
    except Exception as exc:
        return f"ERROR: SQL query failed: {exc}"


def describe_table(table_name: str = "sales") -> str:
    """
    Describe the column schema of a SQLite table.
    The database is at outputs/day3.db.
    """
    db_file = Path(DB_PATH)
    if not db_file.exists():
        return (
            "ERROR: Database not found. "
            "Call load_csv_into_sqlite first to initialise it."
        )
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return f"ERROR: Table '{table_name}' not found or is empty."
        lines = ["cid | name | type | notnull | default | pk"]
        for row in rows:
            lines.append(" | ".join(str(x) for x in row))
        return "\n".join(lines)
    except Exception as exc:
        return f"ERROR: Could not describe table: {exc}"

```

## FILE: ./tools/file_agent.py

```py
from pathlib import Path
import pandas as pd


def read_text_file(file_path: str) -> str:
    """Read a UTF-8 text file and return its content."""
    path = Path(file_path)
    if not path.exists():
        return f"ERROR: File not found: {file_path}"
    if not path.is_file():
        return f"ERROR: Not a file: {file_path}"
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        return f"ERROR: Could not read file: {exc}"


def write_text_file(file_path: str, content: str) -> str:
    """Write UTF-8 text content to a file. Creates parent folders if needed."""
    path = Path(file_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"SUCCESS: Wrote text file to {file_path}"
    except Exception as exc:
        return f"ERROR: Could not write file: {exc}"


def read_csv_preview(file_path: str, rows: int = 5) -> str:
    """Read a CSV file and return a small preview with shape and columns."""
    path = Path(file_path)
    if not path.exists():
        return f"ERROR: CSV not found: {file_path}"
    try:
        df = pd.read_csv(path)
        preview = df.head(rows).to_string(index=False)
        return (
            f"CSV_PATH: {file_path}\n"
            f"ROWS: {len(df)}\n"
            f"COLUMNS: {list(df.columns)}\n"
            f"PREVIEW:\n{preview}"
        )
    except Exception as exc:
        return f"ERROR: Could not read CSV: {exc}"


def list_files_in_directory(directory_path: str = ".") -> str:
    """List files and folders inside a directory."""
    path = Path(directory_path)
    if not path.exists():
        return f"ERROR: Directory not found: {directory_path}"
    if not path.is_dir():
        return f"ERROR: Not a directory: {directory_path}"
    items = sorted([p.name for p in path.iterdir()])
    return "\n".join(items) if items else "Directory is empty."

```

## FILE: ./tools/__init__.py

```py

```

