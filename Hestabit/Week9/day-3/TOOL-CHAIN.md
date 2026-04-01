# TOOL-CHAIN

## Day 3 Goal
Build tool-calling agents for:
- File operations (read, write, preview)
- SQLite operations (load, describe, query)
- Python analysis (pandas insights, top-N ranking)

## Deliverables
- `main.py` — orchestration entry point
- `tools/code_executor.py` — Python analysis tools
- `tools/db_agent.py` — SQLite tools
- `tools/file_agent.py` — file I/O tools
- `TOOL-CHAIN.md` — this document

---

## Architecture

```
User Query
    │
    ▼
Orchestrator (main.py)
    │
    ├──► File Agent  ──► [read_csv_preview, list_files, read_text, write_text]
    │
    ├──► DB Agent    ──► [load_csv_into_sqlite, describe_table, run_sql_query]
    │
    ├──► Code Agent  ──► [analyze_sales_csv, compute_top_n_products]
    │
    └──► Report Agent (no tools — synthesis only)
             │
             ▼
        Final Answer
```

---

## Agents

### 1. File Agent
**Tools:** `list_files_in_directory`, `read_text_file`, `write_text_file`, `read_csv_preview`  
**Job:** Inspect the CSV — report row count, columns, and a brief data description.  
**Terminator:** `FILE_AGENT_DONE`

### 2. DB Agent
**Tools:** `load_csv_into_sqlite`, `describe_table`, `run_sql_query`  
**Job:** Run a revenue-by-region SQL GROUP BY query and summarize results.  
**Terminator:** `DB_AGENT_DONE`

> Note: `load_csv_into_sqlite` is pre-called by the orchestrator before agents run.
> It is also registered as a DB Agent tool so the agent can re-initialize if needed.

### 3. Code Agent
**Tools:** `analyze_sales_csv`, `compute_top_n_products`  
**Job:** Produce business insights (total revenue, top product, top region, avg order value, lowest region) and top-5 product ranking by revenue.  
**Terminator:** `CODE_AGENT_DONE`

### 4. Report Agent
**Tools:** None (reasoning only)  
**Job:** Synthesize all agent outputs into a structured report:
1. Dataset Overview
2. Top 5 Business Insights
3. Recommended Next Action  
**Terminator:** `TERMINATE`

---

## Key Design Decisions

| Decision              | Choice             | Reason                                                                         |
|-----------------------|--------------------|--------------------------------------------------------------------------------|
| `reflect_on_tool_use` | `True`             | Agents reason about tool output before responding — produces cleaner summaries |
| `parallel_tool_calls` | `False`            | Local models handle one tool call at a time reliably                           |
| `buffer_size`         | `10`               | Retains enough context for tool result + response without overflow             |
| `max_tokens`          | `512`              | Enough for structured tool output; avoids truncation of results                |
| DB pre-load           | Orchestrator       | DB Agent focuses on querying, not setup                                        |
| Tool registration     | All 3 db functions | Agent can self-recover if DB is missing                                        |

---

## Why This Matches Day 3 Requirements

- ✅ Agents use real registered tools (function calling)
- ✅ No paid external APIs — runs fully local via LM Studio
- ✅ Python execution via `analyze_sales_csv` / `compute_top_n_products`
- ✅ SQLite querying via `run_sql_query`
- ✅ File read/write via `read_csv_preview` / `write_text_file`
- ✅ Orchestrator delegates to specialist agents
- ✅ Report Agent syntheses all outputs

---

## AutoGen Usage
- `AssistantAgent` — all 4 agents
- Python functions as tools (registered directly)
- `OpenAIChatCompletionClient` with LM Studio local endpoint
- `reflect_on_tool_use=True` — agents summarize tool results
- `BufferedChatCompletionContext(buffer_size=10)` — rolling context window

---

## Running Locally

```bash
# 1. Install dependencies
pip install autogen-agentchat autogen-ext[openai] pandas

# 2. Start LM Studio with a function-calling model
#    e.g. Qwen2.5-7B-Instruct, Phi-3-mini, Mistral-7B-Instruct

# 3. Set environment variables
export MODEL_NAME="qwen2.5-7b-instruct"
export BASE_URL="http://localhost:1234/v1"
export API_KEY="lm-studio"

# 4. Run
python main.py
```

## Environment Variables

| Variable          | Default      | Description                           |
|-------------------|--------------|---------------------------------------|
| `MODEL_NAME`      | _(required)_ | LM Studio model name                  |
| `BASE_URL`        | _(required)_ | LM Studio API URL                     |
| `API_KEY`         | `lm-studio`  | API key (any string for local)        |
| `TEMPERATURE`     | `0.05`       | Low temp for deterministic tool calls |
| `MAX_TOKENS`      | `512`        | Max tokens per agent response         |
| `TIMEOUT_SECONDS` | `120`        | Per-agent timeout                     |
