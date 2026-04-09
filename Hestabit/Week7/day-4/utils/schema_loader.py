import sqlite3
from pathlib import Path
from typing import Any


def get_sqlite_connection(db_path: str | Path) -> sqlite3.Connection:
    """
    Create a SQLite connection.

    Raises:
        FileNotFoundError: if the database file does not exist.
    """
    db_path = Path(db_path)

    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def list_user_tables(connection: sqlite3.Connection) -> list[str]:
    """
    Return user-defined table names from a SQLite database.
    """
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
        """
    )
    return [row["name"] for row in cursor.fetchall()]


def get_table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> list[dict[str, Any]]:
    """
    Return column metadata for a table using PRAGMA table_info.
    """
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    rows = cursor.fetchall()

    columns: list[dict[str, Any]] = []
    for row in rows:
        columns.append(
            {
                "cid": row["cid"],
                "name": row["name"],
                "type": row["type"],
                "notnull": bool(row["notnull"]),
                "default_value": row["dflt_value"],
                "primary_key": bool(row["pk"]),
            }
        )

    return columns


def get_table_foreign_keys(
    connection: sqlite3.Connection,
    table_name: str,
) -> list[dict[str, Any]]:
    """
    Return foreign key metadata for a table using PRAGMA foreign_key_list.
    """
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA foreign_key_list('{table_name}')")
    rows = cursor.fetchall()

    foreign_keys: list[dict[str, Any]] = []
    for row in rows:
        foreign_keys.append(
            {
                "id": row["id"],
                "seq": row["seq"],
                "referenced_table": row["table"],
                "from_column": row["from"],
                "to_column": row["to"],
                "on_update": row["on_update"],
                "on_delete": row["on_delete"],
                "match": row["match"],
            }
        )

    return foreign_keys


def load_sqlite_schema(db_path: str | Path) -> dict[str, Any]:
    """
    Load schema information for all user tables in a SQLite database.
    """
    connection = get_sqlite_connection(db_path)
    tables = list_user_tables(connection)

    schema: dict[str, Any] = {
        "database": str(db_path),
        "dialect": "sqlite",
        "tables": [],
    }

    for table_name in tables:
        schema["tables"].append(
            {
                "table_name": table_name,
                "columns": get_table_columns(connection, table_name),
                "foreign_keys": get_table_foreign_keys(connection, table_name),
            }
        )

    connection.close()
    return schema


def format_schema_for_prompt(schema: dict[str, Any]) -> str:
    """
    Convert structured schema into a compact prompt-friendly text block.
    """
    lines: list[str] = []

    for table in schema.get("tables", []):
        lines.append(f"Table: {table['table_name']}")
        lines.append("Columns:")

        for column in table.get("columns", []):
            line = f"  - {column['name']} ({column['type']})"
            if column["primary_key"]:
                line += " [PRIMARY KEY]"
            if column["notnull"]:
                line += " [NOT NULL]"
            lines.append(line)

        foreign_keys = table.get("foreign_keys", [])
        if foreign_keys:
            lines.append("Foreign Keys:")
            for foreign_key in foreign_keys:
                lines.append(
                    f"  - {foreign_key['from_column']} -> "
                    f"{foreign_key['referenced_table']}.{foreign_key['to_column']}"
                )

        lines.append("")

    return "\n".join(lines).strip()


def get_schema_table_names(schema: dict[str, Any]) -> list[str]:
    """
    Return a simple list of table names from the schema.
    """
    return [table["table_name"] for table in schema.get("tables", [])]