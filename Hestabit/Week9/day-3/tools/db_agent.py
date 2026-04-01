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
