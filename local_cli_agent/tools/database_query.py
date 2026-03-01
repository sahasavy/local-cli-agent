"""
Tool: database_query

Executes SQL queries against a SQLite database.
Supports SELECT for reading and INSERT/UPDATE/DELETE/CREATE for writing.
"""

import sqlite3
from pathlib import Path

from .base import BaseTool

MAX_ROWS = 100


class DatabaseQueryTool(BaseTool):

    def __init__(self, database_path: Path | None = None):
        self._database_path = database_path

    @property
    def name(self) -> str:
        return "database_query"

    @property
    def description(self) -> str:
        db = self._database_path or "in-memory"
        return (
            f"Execute a SQL query against a SQLite database ({db}). "
            "Supports SELECT, INSERT, UPDATE, DELETE, and CREATE TABLE. "
            "Returns results as a formatted table for SELECT queries."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The SQL query to execute.",
                },
                "database": {
                    "type": "string",
                    "description": (
                        "Path to the SQLite database file. "
                        "Uses the configured default if omitted."
                    ),
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs) -> str:
        query: str = kwargs["query"]
        db_override: str | None = kwargs.get("database")

        db_path = db_override or (
            str(self._database_path) if self._database_path else ":memory:"
        )

        if db_path != ":memory:":
            path = Path(db_path)
            path.parent.mkdir(parents=True, exist_ok=True)

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)

            is_select = query.strip().upper().startswith("SELECT")

            if is_select:
                rows = cursor.fetchmany(MAX_ROWS + 1)
                if not rows:
                    conn.close()
                    return "Query returned 0 rows."

                columns = rows[0].keys()
                truncated = len(rows) > MAX_ROWS
                display_rows = rows[:MAX_ROWS]

                col_widths = {col: len(col) for col in columns}
                for row in display_rows:
                    for col in columns:
                        col_widths[col] = max(col_widths[col], len(str(row[col])))

                header = " | ".join(col.ljust(col_widths[col]) for col in columns)
                separator = "-+-".join("-" * col_widths[col] for col in columns)
                lines = [header, separator]
                for row in display_rows:
                    lines.append(
                        " | ".join(
                            str(row[col]).ljust(col_widths[col]) for col in columns
                        )
                    )

                suffix = "+ (truncated)" if truncated else ""
                result = "\n".join(lines)
                conn.close()
                return f"{len(display_rows)}{suffix} rows\n\n{result}"
            else:
                conn.commit()
                affected = cursor.rowcount
                conn.close()
                return f"Query executed successfully. Rows affected: {affected}"

        except sqlite3.Error as exc:
            return f"SQL error: {exc}"
        except Exception as exc:
            return f"Error: {exc}"
