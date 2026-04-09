import re
from typing import Any


SQL_GENERATION_SYSTEM_PROMPT = """
You are a schema-aware SQL generation assistant.

Your job is to convert a natural language question into a safe, read-only SQL query.

Rules:
1. Use only tables and columns present in the provided schema.
2. Generate only SELECT or WITH queries.
3. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, ATTACH, DETACH, or PRAGMA.
4. Prefer explicit column names over SELECT *.
5. Add LIMIT 100 if the query could otherwise return a very large result set.
6. If the schema is insufficient to answer the question safely, respond with:
   UNSUPPORTED_SCHEMA
""".strip()


def clean_question(question: str) -> str:
    """Normalize the incoming natural language question."""
    return question.strip()


def extract_year(question: str) -> str | None:
    """Extract a 4-digit year if present."""
    match = re.search(r"\b(19|20)\d{2}\b", question)
    return match.group(0) if match else None


def build_sql_prompt(question: str, schema_text: str) -> str:
    """
    Build a schema-aware SQL generation prompt.

    This is useful if you later replace the fallback generator with an LLM.
    """
    return f"""
{SQL_GENERATION_SYSTEM_PROMPT}

Schema:
{schema_text}

User Question:
{question}

Return only SQL.
""".strip()


def find_candidate_tables(schema: dict[str, Any], question: str) -> list[dict[str, Any]]:
    """
    Find tables whose names or columns overlap with question keywords.
    """
    question_lower = question.lower()
    keywords = set(re.findall(r"[a-zA-Z_]+", question_lower))

    candidates: list[tuple[int, dict[str, Any]]] = []

    for table in schema.get("tables", []):
        score = 0
        table_name = table["table_name"].lower()

        for keyword in keywords:
            if keyword in table_name:
                score += 3

        for column in table.get("columns", []):
            column_name = column["name"].lower()
            for keyword in keywords:
                if keyword in column_name:
                    score += 2

        if score > 0:
            candidates.append((score, table))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in candidates]


def choose_first_table(schema: dict[str, Any]) -> dict[str, Any] | None:
    """
    Return the first table in the schema if no keyword match exists.
    """
    tables = schema.get("tables", [])
    return tables[0] if tables else None


def choose_display_columns(table: dict[str, Any], max_columns: int = 5) -> list[str]:
    """
    Choose a small number of display columns for a safe fallback SELECT.
    """
    columns = [column["name"] for column in table.get("columns", [])]
    return columns[:max_columns]


def choose_date_column(table: dict[str, Any]) -> str | None:
    """
    Find a likely date/time column.
    """
    for column in table.get("columns", []):
        name = column["name"].lower()
        if "date" in name or "time" in name or "year" in name or "created" in name:
            return column["name"]
    return None


def build_fallback_select_sql(question: str, schema: dict[str, Any]) -> dict[str, Any]:
    """
    Build a safe fallback SQL query using schema inspection.

    This is intentionally conservative:
    - selects from the best candidate table
    - optionally filters by year if a suitable date column exists
    - limits results
    """
    question = clean_question(question)
    year = extract_year(question)

    candidate_tables = find_candidate_tables(schema, question)
    selected_table = candidate_tables[0] if candidate_tables else choose_first_table(schema)

    if selected_table is None:
        raise ValueError("No usable tables found in schema.")

    selected_columns = choose_display_columns(selected_table)
    if not selected_columns:
        raise ValueError("Selected table has no usable columns.")

    date_column = choose_date_column(selected_table)

    where_clause = ""
    if year and date_column:
        where_clause = f"WHERE strftime('%Y', {date_column}) = '{year}'"

    sql = f"""
SELECT
    {", ".join(selected_columns)}
FROM {selected_table['table_name']}
{where_clause}
LIMIT 100;
""".strip()

    return {
        "sql": sql,
        "strategy": "schema_safe_fallback",
        "reasoning": {
            "selected_table": selected_table["table_name"],
            "selected_columns": selected_columns,
            "date_column": date_column,
            "year": year,
        },
    }


def generate_sql(question: str, schema: dict[str, Any]) -> dict[str, Any]:
    """
    Generate SQL from a natural language question using a schema-safe strategy.

    Current design:
    - builds an LLM-ready prompt
    - returns a conservative fallback SQL query
    - does not assume a fixed business schema
    """
    cleaned_question = clean_question(question)

    schema_lines: list[str] = []
    for table in schema.get("tables", []):
        schema_lines.append(f"Table: {table['table_name']}")
        for column in table.get("columns", []):
            schema_lines.append(f"  - {column['name']} ({column['type']})")

    prompt = build_sql_prompt(cleaned_question, "\n".join(schema_lines))
    fallback = build_fallback_select_sql(cleaned_question, schema)

    return {
        "question": cleaned_question,
        "prompt": prompt,
        "sql": fallback["sql"],
        "strategy": fallback["strategy"],
        "reasoning": fallback["reasoning"],
    }