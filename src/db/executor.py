import traceback
from typing import Any

import psycopg2
import psycopg2.extras

from src.db.config import db_config


# ── Execute SQL ───────────────────────────────────────────────────────────────
def execute_sql(sql: str) -> dict[str, Any]:
    """
    Execute a SQL query against PostgreSQL and return results.

    Returns a dict with:
        - success: bool
        - rows: list of dicts (column_name -> value)
        - row_count: number of rows returned
        - columns: list of column names
        - error: error message if failed (None if success)
    """
    conn = None
    try:
        conn = psycopg2.connect(db_config.connection_string)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return {
                "success": True,
                "rows": [dict(row) for row in rows],
                "row_count": len(rows),
                "columns": columns,
                "error": None,
            }

    except Exception as e:
        return {
            "success": False,
            "rows": [],
            "row_count": 0,
            "columns": [],
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    finally:
        if conn:
            conn.close()


# ── Format Results ────────────────────────────────────────────────────────────
def format_results(result: dict[str, Any], max_rows: int = 20) -> str:
    """
    Format execution results into a readable string for display.
    """
    if not result["success"]:
        return f"❌ SQL Error:\n{result['error']}"

    if result["row_count"] == 0:
        return "✅ Query executed successfully. No rows returned."

    rows = result["rows"][:max_rows]
    columns = result["columns"]

    # Build table header
    header = " | ".join(columns)
    separator = "-+-".join("-" * len(col) for col in columns)
    lines = [header, separator]

    # Build rows
    for row in rows:
        line = " | ".join(str(row.get(col, "")) for col in columns)
        lines.append(line)

    output = "\n".join(lines)

    if result["row_count"] > max_rows:
        output += f"\n\n... showing {max_rows} of {result['row_count']} rows"

    return f"✅ {result['row_count']} row(s) returned:\n\n{output}"
