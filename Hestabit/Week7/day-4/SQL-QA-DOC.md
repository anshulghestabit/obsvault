
---
# SQL Question Answering System — Day 4

## Overview

This Day 4 system implements a **Text → SQL → Answer pipeline**.

The system converts natural language questions into SQL queries, validates them for safety, executes them on a database, and summarizes the results.

This implementation is **schema-aware and schema-safe**, meaning:

* it dynamically reads database structure
* it does not assume fixed table/column names
* it avoids unsafe SQL operations

---

## Deliverables

* `src/pipelines/sql_pipeline.py`
* `src/generator/sql_generator.py`
* `src/utils/schema_loader.py`
* `Readme/Day-4/SQL-QA-DOC.md`

---

## Learning Outcomes Covered

* Convert natural language queries into SQL
* Perform schema-aware reasoning
* Validate SQL queries for safety
* Execute queries in a secure manner
* Summarize tabular results into readable output

---

## System Architecture

The system is divided into three main components:

### 1. Schema Loader

**File:** `src/utils/schema_loader.py`

Responsibilities:

* Connect to SQLite database
* Extract:

  * table names
  * column metadata
  * primary keys
  * foreign keys
* Provide structured schema representation
* Format schema into prompt-friendly text

Key benefit:

* Enables **automatic schema discovery**
* Makes system adaptable to any database

---

### 2. SQL Generator

**File:** `src/generator/sql_generator.py`

Responsibilities:

* Normalize the user question
* Inspect schema dynamically
* Build a schema-aware SQL generation prompt
* Generate SQL using a **safe fallback strategy**

### Current Strategy

Instead of hardcoding assumptions like:

* `sales` table
* `artist` column

The generator:

1. Finds candidate tables using keyword overlap
2. Selects relevant columns
3. Adds filters (e.g., year) only if valid
4. Limits output using `LIMIT 100`

### Important Design Decision

This generator is:

* **schema-safe**
* **not hardcoded**
* **LLM-ready**

It can later be replaced with:

* OpenAI / local LLM SQL generation
* prompt-based SQL synthesis

Without changing pipeline structure

---

### 3. SQL Pipeline (Orchestrator)

**File:** `src/pipelines/sql_pipeline.py`

Responsibilities:

* Load schema
* Generate SQL
* Validate SQL
* Execute SQL
* Summarize results

This is the **end-to-end system entry point**.

---

## Core Features

### Auto Schema Loader

* Automatically detects:

  * tables
  * columns
  * relationships
* No manual schema input required

---

### SQL Validation (Security)

The system ensures safe execution.

Allowed:

* `SELECT`
* `WITH`

Blocked:

* `DROP`
* `DELETE`
* `TRUNCATE`
* `ALTER`
* `UPDATE`
* `INSERT`
* `PRAGMA`
* database attach/detach

This prevents:

* SQL injection
* destructive queries

---

### Safe Execution

* Uses SQLite connection
* Executes only validated queries
* Returns:

  * column names
  * row data

---

### Result Summarization

Instead of raw SQL output, the system provides:

* number of rows returned
* column names
* preview of top rows
* human-readable format

---

## Example Flow

User input:

```text
Show total sales by artist for 2023
```

System execution:

1. Load schema from database
2. Analyze question
3. Select candidate table(s)
4. Generate SQL query
5. Validate query safety
6. Execute query
7. Summarize results

---

## Example Command

```bash
python src/pipelines/sql_pipeline.py \
  --db-path data/example.db \
  --question "Show total sales by artist for 2023"
```

---

## Output Structure

The system returns:

* question
* generated SQL
* validation message
* schema preview
* result columns
* result rows
* summary
* reasoning (table/column selection)
* generator prompt (for debugging / LLM upgrade)

---

## Design Principles

This system follows:

* Explicit is better than implicit
* Schema-aware over hardcoded logic
* Safe execution over flexibility
* Modular design for easy upgrades
* Separation of concerns:

  * schema loading
  * SQL generation
  * execution

---

## Limitations

Current implementation is intentionally simple:

* SQL generation is rule-based (not LLM)
* complex joins are limited
* aggregation logic is basic
* only SQLite supported (for now)

These are acceptable trade-offs for Day 4.

---

## Future Improvements

Possible upgrades:

* LLM-based SQL generation (OpenAI / local models)
* PostgreSQL support
* SQL correction loop (retry on errors)
* better join inference
* semantic column matching
* query explanation output

---

## Outcome

This Day 4 system provides a complete baseline for:

* Natural language → SQL conversion
* Schema-aware query generation
* Safe database interaction
* Result summarization

It is designed to be:

* extensible
* safe
* compatible with production-style pipelines

---

## Final Note

This implementation avoids fake assumptions about schema structure and instead builds a **robust, general-purpose SQL-QA system**, making it suitable for real-world datasets and future LLM integration.

---
