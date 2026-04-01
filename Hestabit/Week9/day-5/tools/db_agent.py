from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

from autogen_core import MessageContext, RoutedAgent, message_handler

from models.day3_messages import DBInspection, FileInspection
from utils.day3_helpers import parse_json


DATA_DIR = Path("data").resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)


def preview_csv(csv_path: str, limit: int = 5) -> str:
    """Preview CSV rows."""
    file_path = Path(csv_path).resolve()
    if not file_path.exists():
        return json.dumps({"error": f"CSV not found: {file_path}"}, indent=2)

    try:
        rows = []
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if idx >= limit:
                    break
                rows.append(row)
        return json.dumps({"rows": rows, "preview_count": len(rows)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def csv_columns(csv_path: str) -> str:
    """Return CSV columns."""
    file_path = Path(csv_path).resolve()
    if not file_path.exists():
        return json.dumps({"error": f"CSV not found: {file_path}"}, indent=2)

    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
        return json.dumps({"columns": headers}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def csv_schema(csv_path: str, sample_rows: int = 25) -> str:
    """Infer CSV schema."""
    file_path = Path(csv_path).resolve()
    if not file_path.exists():
        return json.dumps({"error": f"CSV not found: {file_path}"}, indent=2)

    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = []
            for idx, row in enumerate(reader):
                if idx >= sample_rows:
                    break
                rows.append(row)

        schema = []
        for col in headers:
            values = [str(r.get(col, "")).strip() for r in rows]
            non_empty = [v for v in values if v != ""]
            numeric_count = 0
            for v in non_empty:
                try:
                    float(v.replace(",", ""))
                    numeric_count += 1
                except Exception:
                    pass

            if non_empty and numeric_count == len(non_empty):
                inferred = "numeric"
            elif non_empty:
                inferred = "text"
            else:
                inferred = "unknown"

            schema.append(
                {
                    "column": col,
                    "inferred_type": inferred,
                    "non_empty_sample_count": len(non_empty),
                }
            )

        return json.dumps({"schema": schema}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def import_csv_to_sqlite(
    csv_path: str,
    db_path: str = "data/day3_temp.sqlite",
    table_name: str = "data_table",
) -> str:
    """Import CSV into SQLite."""
    csv_file = Path(csv_path).resolve()
    db_file = Path(db_path).resolve()

    if not csv_file.exists():
        return json.dumps({"error": f"CSV not found: {csv_file}"}, indent=2)

    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()

        with open(csv_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)

            cols = ", ".join([f'"{h}" TEXT' for h in headers])
            cur.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            cur.execute(f'CREATE TABLE "{table_name}" ({cols})')

            placeholders = ", ".join(["?"] * len(headers))
            insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'
            cur.executemany(insert_sql, reader)

        conn.commit()
        cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        row_count = cur.fetchone()[0]
        conn.close()

        return json.dumps(
            {
                "status": "ok",
                "db_path": str(db_file),
                "table_name": table_name,
                "rows_imported": row_count,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def list_sqlite_tables(db_path: str) -> str:
    """List SQLite tables."""
    db_file = Path(db_path).resolve()
    if not db_file.exists():
        return json.dumps({"error": f"Database not found: {db_file}"}, indent=2)

    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        rows = [row[0] for row in cur.fetchall()]
        conn.close()
        return json.dumps({"tables": rows}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def sqlite_table_schema(db_path: str, table_name: str) -> str:
    """Return SQLite table schema."""
    db_file = Path(db_path).resolve()
    if not db_file.exists():
        return json.dumps({"error": f"Database not found: {db_file}"}, indent=2)

    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute(f'PRAGMA table_info("{table_name}")')
        rows = cur.fetchall()
        conn.close()

        columns = [
            {
                "cid": r[0],
                "name": r[1],
                "type": r[2],
                "notnull": r[3],
                "default_value": r[4],
                "pk": r[5],
            }
            for r in rows
        ]
        return json.dumps({"table_name": table_name, "columns": columns}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def sqlite_table_preview(db_path: str, table_name: str, limit: int = 5) -> str:
    """Preview SQLite rows."""
    db_file = Path(db_path).resolve()
    if not db_file.exists():
        return json.dumps({"error": f"Database not found: {db_file}"}, indent=2)

    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM "{table_name}" LIMIT {int(limit)}')
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return json.dumps({"table_name": table_name, "rows": rows}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def query_sqlite(db_path: str, sql: str) -> str:
    """Run SQLite query."""
    db_file = Path(db_path).resolve()
    if not db_file.exists():
        return json.dumps({"error": f"Database not found: {db_file}"}, indent=2)

    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return json.dumps({"rows": rows, "count": len(rows)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


class DBAgent(RoutedAgent):
    def __init__(self, name: str, debug_mode: bool = False) -> None:
        super().__init__(name)
        self._debug_mode = debug_mode

    def _debug(self, text: str) -> None:
        if self._debug_mode:
            print(text)

    @message_handler
    async def handle_file_inspection(self, message: FileInspection, ctx: MessageContext) -> DBInspection:
        self._debug("[db_agent] started")

        columns: list[str] = []
        preview_rows: list[dict[str, Any]] = []
        db_path = ""
        table_name = ""

        if message.intent == "code_generation":
            summary = "DB inspection not needed for code generation."
        elif not message.exists:
            summary = "No file available for DB/CSV inspection."
        elif message.file_type == "csv":
            columns_info = parse_json(csv_columns(message.file_path))
            schema_info = parse_json(csv_schema(message.file_path))
            preview_info = parse_json(preview_csv(message.file_path, limit=5))
            import_info = parse_json(import_csv_to_sqlite(message.file_path))

            columns = columns_info.get("columns", []) or []
            preview_rows = preview_info.get("rows", []) or []
            db_path = str(import_info.get("db_path", ""))
            table_name = str(import_info.get("table_name", ""))

            summary = (
                f"CSV columns: {columns}\n"
                f"Schema sample: {schema_info.get('schema', [])[:5]}\n"
                f"Preview rows count: {len(preview_rows)}\n"
                f"Imported DB path: {db_path}\n"
                f"Imported table: {table_name}"
            )

        elif message.file_type == "sqlite":
            tables_info = parse_json(list_sqlite_tables(message.file_path))
            tables = tables_info.get("tables", []) or []

            db_path = message.file_path
            table_name = str(tables[0]) if tables else ""

            schema_info = parse_json(sqlite_table_schema(db_path, table_name)) if table_name else {}
            preview_info = parse_json(sqlite_table_preview(db_path, table_name, limit=5)) if table_name else {}

            columns = [c["name"] for c in schema_info.get("columns", [])] if schema_info else []
            preview_rows = preview_info.get("rows", []) if preview_info else []

            summary = (
                f"SQLite tables: {tables}\n"
                f"Chosen table: {table_name}\n"
                f"Columns: {columns}\n"
                f"Preview rows count: {len(preview_rows)}"
            )
        else:
            summary = "Structured DB/CSV inspection not applicable to this file."

        self._debug("[db_agent] finished")

        return DBInspection(
            query=message.query,
            intent=message.intent,
            file_path=message.file_path,
            output_path=message.output_path,
            file_type=message.file_type,
            requested_items=message.requested_items,
            columns=columns,
            preview=preview_rows,
            db_path=db_path,
            table_name=table_name,
            summary=summary,
        )