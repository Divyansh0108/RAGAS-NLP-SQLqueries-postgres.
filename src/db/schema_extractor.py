import psycopg2
from psycopg2.extras import RealDictCursor
import json
from pathlib import Path
from .config import db_config


def extract_schema():
    """Extract schema metadata from PostgreSQL database"""
    conn = psycopg2.connect(db_config.connection_string)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get all tables
    cursor.execute(
        """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """
    )
    tables = cursor.fetchall()

    schema_docs = {}

    for table in tables:
        table_name = table["table_name"]

        # Get columns
        cursor.execute(
            """
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position;
        """,
            (table_name,),
        )
        columns = cursor.fetchall()

        # Get primary keys
        cursor.execute(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = %s 
                AND tc.constraint_type = 'PRIMARY KEY';
        """,
            (table_name,),
        )
        primary_keys = [row["column_name"] for row in cursor.fetchall()]

        # Get foreign keys
        cursor.execute(
            """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_name = %s 
                AND tc.constraint_type = 'FOREIGN KEY';
        """,
            (table_name,),
        )
        foreign_keys = cursor.fetchall()

        schema_docs[table_name] = {
            "table_name": table_name,
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
        }

    cursor.close()
    conn.close()

    # Save to file — path anchored to project root, not CWD
    output_path = (
        Path(__file__).resolve().parents[2] / "data/schema_docs/dvdrental_schema.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(schema_docs, f, indent=2, default=str)

    print(f"Schema extracted and saved to {output_path}")
    return schema_docs


if __name__ == "__main__":
    extract_schema()
