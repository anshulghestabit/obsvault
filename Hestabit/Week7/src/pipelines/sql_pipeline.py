import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.generator.sql_generator import generate_sql  # noqa: E402
from src.utils.schema_loader import (  # noqa: E402
    format_schema_for_prompt,
    get_sqlite_connection,
    load_sqlite_schema,
)


ALLOWED_SQL_PREFIXES = ("select", "with")
FORBIDDEN_SQL_PATTERNS = (
    "drop ",
    "delete ",
    "truncate ",
    "alter ",
    "update ",
    "insert ",
    "attach database",
    "detach database",
    "pragma ",
)


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate SQL for safe read-only execution.
    """
    normalized_sql = sql.strip().lower()

    if not normalized_sql:
        return False, "SQL query is empty."

    if not normalized_sql.startswith(ALLOWED_SQL_PREFIXES):
        return False, "Only SELECT or WITH queries are allowed."

    for pattern in FORBIDDEN_SQL_PATTERNS:
        if pattern in normalized_sql:
            return False, f"Forbidden SQL pattern detected: {pattern.strip()}"

    return True, "SQL validation passed."


def execute_sql(
    db_path: str | Path,
    sql: str,
) -> tuple[list[str], list[tuple[Any, ...]]]:
    """
    Execute validated SQL and return columns and rows.
    """
    connection = get_sqlite_connection(db_path)
    cursor = connection.cursor()

    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description] if cursor.description else []

    connection.close()
    return columns, [tuple(row) for row in rows]


def summarize_results(columns: list[str], rows: list[tuple[Any, ...]]) -> str:
    """
    Build a simple result summary.
    """
    if not rows:
        return "The query returned no rows."

    summary_lines = [
        f"Returned {len(rows)} row(s).",
        f"Columns: {', '.join(columns)}",
    ]

    preview_count = min(5, len(rows))
    summary_lines.append(f"Previewing first {preview_count} row(s):")

    for row in rows[:preview_count]:
        row_summary = ", ".join(
            f"{column}={value}" for column, value in zip(columns, row, strict=False)
        )
        summary_lines.append(f"- {row_summary}")

    return "\n".join(summary_lines)


def build_sql_pipeline_output(
    db_path: str | Path,
    question: str,
) -> dict[str, Any]:
    """
    Full Day 4 pipeline:
    - load schema
    - generate SQL
    - validate SQL
    - execute SQL
    - summarize results
    """
    schema = load_sqlite_schema(db_path)
    generated = generate_sql(question=question, schema=schema)

    sql = generated["sql"]
    is_valid, validation_message = validate_sql(sql)

    if not is_valid:
        raise ValueError(f"SQL validation failed: {validation_message}")

    columns, rows = execute_sql(db_path, sql)
    summary = summarize_results(columns, rows)

    return {
        "question": question,
        "generated_sql": sql,
        "generation_strategy": generated["strategy"],
        "generation_reasoning": generated["reasoning"],
        "validation_message": validation_message,
        "schema_preview": format_schema_for_prompt(schema),
        "columns": columns,
        "rows": rows,
        "summary": summary,
        "generator_prompt": generated["prompt"],
    }


def print_pipeline_output(output: dict[str, Any]) -> None:
    """
    Pretty-print pipeline result.
    """
    print("\nQuestion:")
    print(output["question"])

    print("\nGeneration Strategy:")
    print(output["generation_strategy"])

    print("\nGenerated SQL:")
    print(output["generated_sql"])

    print("\nValidation:")
    print(output["validation_message"])

    print("\nReasoning:")
    print(json.dumps(output["generation_reasoning"], indent=2, ensure_ascii=False))

    print("\nSummary:")
    print(output["summary"])


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run the Day 4 SQL Question Answering pipeline."
    )
    parser.add_argument(
        "--db-path",
        type=str,
        required=True,
        help="Path to SQLite database file.",
    )
    parser.add_argument(
        "--question",
        type=str,
        required=True,
        help='Natural language question, e.g. "Show total sales by artist for 2023."',
    )
    return parser.parse_args()


def main() -> None:
    """
    Entry point for CLI usage.
    """
    args = parse_args()
    output = build_sql_pipeline_output(
        db_path=args.db_path,
        question=args.question,
    )
    print_pipeline_output(output)


if __name__ == "__main__":
    main()