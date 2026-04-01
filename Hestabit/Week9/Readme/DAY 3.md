# Day 3 — Tool-Calling Multi-Agent System with AutoGen + LM Studio

A multi-agent project built with **AutoGen** and **LM Studio**, where agents do not rely only on prompting — they use **registered tools** for file handling, SQLite queries, and Python/pandas analysis.

This Day 3 system is centered on a sales-analysis workflow using:

- a **File Agent** for CSV inspection
    
- a **DB Agent** for SQL-based analysis
    
- a **Code Agent** for pandas/Python analysis
    
- a **Report Agent** for final synthesis
    

---

## Overview

This project analyzes `data/sales.csv` using three specialist agents and one synthesizer agent.

The orchestrator:

1. prepares the CSV/database context
    
2. asks the File Agent to inspect the dataset
    
3. asks the DB Agent to run a revenue-by-region SQL query
    
4. asks the Code Agent to compute business insights and top products
    
5. sends all outputs to the Report Agent for the final report
    

Unlike Day 1 and Day 2, this project introduces **real tool use** through AutoGen tool registration. That means the agent is not just “pretending” to inspect files or run queries — it can actually call Python functions you registered in `tools/`.

---

## Tech Stack

- Python
    
- AutoGen AgentChat
    
- AutoGen OpenAI extension
    
- LM Studio via OpenAI-compatible API
    
- pandas
    
- sqlite3
    
- asyncio
    

---

## Dependencies

```txt
autogen-agentchat
autogen-ext[openai]
pandas
```

These are the dependencies shown in your uploaded `requirements.txt`.

---

## Project Structure

```text
.
├── data
│   └── sales.csv
├── .env
├── files
├── main_2ndpass.py
├── main.py
├── outputs
│   └── day3.db
├── python_project_dump.md
├── requirements.txt
├── TOOL-CHAIN.md
└── tools
    ├── code_executor.py
    ├── db_agent.py
    ├── file_agent.py
    └── __init__.py
```

This structure comes directly from the uploaded Day 3 dump.

---

## High-Level Architecture

The system uses a hub-and-spoke pattern:

- **Orchestrator (`main.py`)** controls the workflow
    
- **File Agent** uses file tools
    
- **DB Agent** uses SQLite tools
    
- **Code Agent** uses pandas analysis tools
    
- **Report Agent** has no tools and only synthesizes outputs
    

```mermaid
flowchart TD
    U[User Query] --> O[Orchestrator / main.py]
    O --> F[File Agent]
    O --> D[DB Agent]
    O --> C[Code Agent]
    F --> O
    D --> O
    C --> O
    O --> R[Report Agent]
    R --> A[Final Report]
```

That architecture is explicitly described in the code comments and reflected in the actual execution flow.

---

## End-to-End Execution Flow

```mermaid
flowchart TD
    A[User enters query] --> B[run_day3_flow]
    B --> C[build_model_client]
    C --> D[Build File Agent]
    C --> E[Build DB Agent]
    C --> F[Build Code Agent]
    C --> G[Build Report Agent]

    B --> H[Resolve CSV path]
    H --> I[Pre-load CSV into SQLite]
    I --> J[Describe sales table schema]

    J --> K[Ask File Agent]
    K --> L[File output]

    L --> M[Ask DB Agent]
    M --> N[DB output]

    N --> O[Ask Code Agent]
    O --> P[Code output]

    P --> Q[Ask Report Agent]
    Q --> R[Final report]

    R --> S[Print all sections]
    S --> T[Close model client]
```

This flow matches `run_day3_flow()` in `main.py`: preload DB, run the three specialist agents, then synthesize with the report agent.

---

## Tool-Calling Flow

```mermaid
flowchart LR
    FA[File Agent] --> T1[read_csv_preview / list_files / read_text / write_text]
    DBA[DB Agent] --> T2[load_csv_into_sqlite / describe_table / run_sql_query]
    CA[Code Agent] --> T3[analyze_sales_csv / compute_top_n_products]
    RA[Report Agent] --> T4[No tools - synthesis only]
```

This diagram reflects the actual `tools=[...]` registrations in the agent builder functions.

---

## Class / Object Diagram

Your code still mostly uses **functions**, not custom user-defined classes. The runtime is built out of AutoGen classes such as `AssistantAgent`, `OpenAIChatCompletionClient`, `TextMessage`, `BufferedChatCompletionContext`, and `CancellationToken`, while your own modules expose helper functions and registered tools.

```mermaid
classDiagram
    class main_py {
        +get_required_env(name)
        +print_section(title)
        +print_status(message)
        +build_model_client()
        +build_file_agent(model_client)
        +build_db_agent(model_client)
        +build_code_agent(model_client)
        +build_report_agent(model_client)
        +ask_agent(agent, source, prompt, timeout_seconds)
        +run_day3_flow(user_query)
    }

    class main_2ndpass_py {
        +build_model_client(stop)
        +build_file_agent(model_client)
        +build_db_agent(model_client)
        +build_code_agent(model_client)
        +build_report_agent(model_client)
        +ask_agent(agent, source, prompt, timeout_seconds)
        +run_day3_flow(user_query)
    }

    class file_agent_py {
        +read_text_file(file_path)
        +write_text_file(file_path, content)
        +read_csv_preview(file_path, rows)
        +list_files_in_directory(directory_path)
    }

    class db_agent_py {
        +load_csv_into_sqlite(csv_path, table_name)
        +run_sql_query(query)
        +describe_table(table_name)
    }

    class code_executor_py {
        +analyze_sales_csv(csv_path)
        +compute_top_n_products(csv_path, n)
    }

    class OpenAIChatCompletionClient
    class ModelInfo
    class AssistantAgent
    class BufferedChatCompletionContext
    class TextMessage
    class CancellationToken

    main_py --> OpenAIChatCompletionClient : creates
    main_py --> AssistantAgent : builds
    main_py --> TextMessage : sends
    main_py --> CancellationToken : uses

    main_2ndpass_py --> OpenAIChatCompletionClient : creates per agent
    main_2ndpass_py --> AssistantAgent : builds
    main_2ndpass_py --> TextMessage : sends
    main_2ndpass_py --> CancellationToken : uses

    main_py --> file_agent_py : imports tools
    main_py --> db_agent_py : imports tools
    main_py --> code_executor_py : imports tools

    main_2ndpass_py --> file_agent_py : imports tools
    main_2ndpass_py --> db_agent_py : imports tools
    main_2ndpass_py --> code_executor_py : imports tools
```

This reflects both orchestration files plus the three tool modules in your uploaded code.

---

## Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant DB as SQLite Setup
    participant F as File Agent
    participant D as DB Agent
    participant C as Code Agent
    participant R as Report Agent

    U->>O: Enter query
    O->>O: build_model_client()
    O->>DB: load_csv_into_sqlite(csv_path, "sales")
    DB-->>O: preload result
    O->>DB: describe_table("sales")
    DB-->>O: schema

    O->>F: ask_agent(file_prompt)
    F-->>O: file_output

    O->>D: ask_agent(db_prompt)
    D-->>O: db_output

    O->>C: ask_agent(code_prompt)
    C-->>O: code_output

    O->>R: ask_agent(report_prompt)
    R-->>O: final_output

    O->>O: print sections
    O->>O: close model client
```

That sequence is the real orchestration behavior in `main.py`.

---

## Main Files Explained

## `main.py`

This is the primary Day 3 orchestrator.

It is responsible for:

- loading environment configuration
    
- building the model client
    
- building all agents
    
- preloading the CSV into SQLite
    
- describing the schema
    
- calling each specialist agent in sequence
    
- calling the report agent
    
- printing all intermediate outputs
    
- closing the shared model client
    

### Important behavior in `main.py`

- `build_model_client()` enables `function_calling=True`, which is critical because Day 3 depends on tools.
    
- All four agents share the same `model_client`.
    
- `reflect_on_tool_use=True` is enabled for the File, DB, and Code agents in this version.
    
- The orchestrator itself preloads `sales.csv` into SQLite before the DB Agent is asked to query it.
    

---

## `main_2ndpass.py`

This is a second orchestration variant with more local-model control.

The major differences are:

- each agent gets its **own model client**
    
- each client can receive a **stop-token list**
    
- `reflect_on_tool_use=False` is used for File/DB/Code agents
    
- stop sequences like `FILE_AGENT_DONE`, `DB_AGENT_DONE`, `CODE_AGENT_DONE`, and `TERMINATE` are passed through `extra_create_args={"stop": ...}` to stop runaway generation on local models
    

So `main_2ndpass.py` is essentially a more controlled, local-LLM-friendly refinement of the same Day 3 architecture.

---

## `tools/file_agent.py`

This module contains file-oriented tools.

### Functions

- `read_text_file(file_path)`
    
- `write_text_file(file_path, content)`
    
- `read_csv_preview(file_path, rows=5)`
    
- `list_files_in_directory(directory_path=".")`
    

### Purpose

These functions let the File Agent:

- read text files
    
- preview CSV structure
    
- list directory contents
    
- write text outputs if needed
    

The most important Day 3 tool here is `read_csv_preview()`, which returns:

- CSV path
    
- row count
    
- column names
    
- preview rows
    

---

## `tools/db_agent.py`

This module contains SQLite tools.

### Functions

- `load_csv_into_sqlite(csv_path, table_name="sales")`
    
- `run_sql_query(query)`
    
- `describe_table(table_name="sales")`
    

### Purpose

These tools let the DB Agent:

- load a CSV into SQLite
    
- inspect schema
    
- run read-only `SELECT` queries against the local database
    

A very important safety detail is that `run_sql_query()` only allows queries starting with `select`; otherwise it returns `ERROR: Only SELECT queries are allowed.`

The database file path is fixed as `outputs/day3.db`.

---

## `tools/code_executor.py`

This module contains Python/pandas analytics tools.

### Functions

- `analyze_sales_csv(csv_path)`
    
- `compute_top_n_products(csv_path, n=5)`
    

### `analyze_sales_csv(csv_path)`

This function:

- loads the CSV with pandas
    
- verifies required columns
    
- computes `revenue = units * unit_price`
    
- calculates total revenue
    
- total units
    
- top product by revenue
    
- top region by revenue
    
- average transaction revenue
    
- highest-volume product
    
- lowest-revenue region
    

### `compute_top_n_products(csv_path, n=5)`

This function:

- computes revenue per product
    
- sorts descending
    
- returns the top `n` products as text
    

So the Code Agent is your pure Python analytics specialist.

---

## Agent Roles

## File Agent

The File Agent is told to inspect files and preview CSV/text data using tools, especially `read_csv_preview()`. It is explicitly told **not** to do SQL or analysis.

## DB Agent

The DB Agent is responsible for SQL-based reasoning on the already initialized `sales` table. In `main.py`, it is told to use `run_sql_query()` and summarize the result.

## Code Agent

The Code Agent is responsible for pandas-based business insight generation and top-product ranking. It calls `analyze_sales_csv()` and `compute_top_n_products()`.

## Report Agent

The Report Agent has **no tools**. It only combines File Agent, DB Agent, and Code Agent outputs into a final structured report.

---

## Report Format

In `main.py`, the Report Agent is instructed to produce exactly these sections:

1. Dataset Overview
    
2. Top 5 Business Insights
    
3. Recommended Next Action
    

In `main_2ndpass.py`, the formatting is even stricter, with explicit markdown headings and `TERMINATE` as the final stop signal.

---

## Tool Responsibility Diagram

```mermaid
flowchart TD
    CSV[data/sales.csv] --> ORCH[Orchestrator]
    ORCH --> SQLITE[load_csv_into_sqlite]
    SQLITE --> DBFILE[outputs/day3.db]

    ORCH --> FILEA[File Agent]
    FILEA --> PREVIEW[read_csv_preview]

    ORCH --> DBA[DB Agent]
    DBA --> SQL[run_sql_query]
    DBA --> SCHEMA[describe_table]

    ORCH --> CODEA[Code Agent]
    CODEA --> PANDAS1[analyze_sales_csv]
    CODEA --> PANDAS2[compute_top_n_products]

    PREVIEW --> REPORT[Report Agent]
    SQL --> REPORT
    SCHEMA --> REPORT
    PANDAS1 --> REPORT
    PANDAS2 --> REPORT

    REPORT --> FINAL[Final Report]
```

This is the clearest tool-level view of your Day 3 system.

---

## Why Day 3 Is Architecturally Important

Day 3 is the point where your project becomes a real **agent + tools** system instead of a pure prompt-chain system.

The main architectural changes are:

- tool registration
    
- actual file/database/code execution
    
- SQL and pandas working on the same dataset through different specialist paths
    
- synthesis of heterogeneous outputs into one report
    

This is a big step toward production-style agent systems.

---

## Strengths

- real tool-calling agents
    
- clear division of labor
    
- combines structured SQL analysis and pandas analysis
    
- has a final synthesis layer
    
- explicit timeout/error handling in `ask_agent()`
    
- safer SQL because only `SELECT` is allowed
    
- second-pass version improves local model stability with stop sequences
    

---

## Current Limitations

This Day 3 project still does **not** include:

- dynamic planner/orchestrator logic like Day 2
    
- memory across runs
    
- reflection/validator stages in the main Day 3 pipeline
    
- retrieval/RAG
    
- external web search
    
- fully dynamic tool selection beyond the fixed registered tools
    
- parallel agent execution; the File, DB, and Code agents are called sequentially in `run_day3_flow()`
    

So it is a strong tool-calling architecture, but still not a full autonomous agent framework yet.

---

## How to Run

```bash
python main.py
```

The script prompts for a query. If no query is entered, it defaults to:

```text
Analyse sales.csv and generate top 5 insights.
```

That default is defined in both `main.py` and `main_2ndpass.py`.

---

## Simple Mental Model

You can explain Day 3 like this:

- **File Agent** = data inspector
    
- **DB Agent** = SQL analyst
    
- **Code Agent** = Python analyst
    
- **Report Agent** = business presenter
    

The orchestrator coordinates all of them.

---

## Short Summary

Day 3 is a **tool-calling multi-agent sales-analysis system** built with AutoGen and LM Studio. It uses registered Python tools for file inspection, SQLite querying, and pandas analytics, then combines those outputs into a final report. The presence of both `main.py` and `main_2ndpass.py` shows that you also experimented with more stable local-model behavior using stop tokens and reduced reflection.

---

If you want, next I can do a **very simple viva-style explanation** for Day 3 too, exactly the way you would speak it to your instructor.