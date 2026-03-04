import json
import os
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "data" / "schema_docs" / "dvdrental_schema.json"
EXAMPLES_PATH = ROOT / "data" / "examples" / "examples.jsonl"
CHROMA_PATH = ROOT / "data" / "chroma_db"

# ── ChromaDB + Embedding Function ────────────────────────────────────────────
embedding_fn = OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text",
)

client = chromadb.PersistentClient(path=str(CHROMA_PATH))

# ── Collections ──────────────────────────────────────────────────────────────
schema_col = client.get_or_create_collection(
    name="schema_collection",
    embedding_function=embedding_fn,
)

examples_col = client.get_or_create_collection(
    name="examples_collection",
    embedding_function=embedding_fn,
)


# ── 1. Embed Schema ───────────────────────────────────────────────────────────
def embed_schema():
    print("📂 Loading schema...")
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)

    documents, metadatas, ids = [], [], []

    for table in schema.values():
        table_name = table["table_name"]
        columns = ", ".join(
            f"{col['column_name']} ({col['data_type']})" for col in table["columns"]
        )
        foreign_keys = "; ".join(
            f"{fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}"
            for fk in table.get("foreign_keys", [])
        )

        doc = (
            f"Table: {table_name}\n"
            f"Columns: {columns}\n"
            f"Foreign Keys: {foreign_keys if foreign_keys else 'None'}"
        )

        documents.append(doc)
        metadatas.append({"table_name": table_name})
        ids.append(f"schema_{table_name}")

    schema_col.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"✅ Embedded {len(documents)} tables into schema_collection")


# ── 2. Embed Examples ─────────────────────────────────────────────────────────
def embed_examples():
    print("📂 Loading examples...")
    documents, metadatas, ids = [], [], []

    with open(EXAMPLES_PATH) as f:
        for line in f:
            ex = json.loads(line.strip())
            doc = f"Question: {ex['question']}\nSQL: {ex['sql']}"
            documents.append(doc)
            metadatas.append(
                {
                    "id": ex["id"],
                    "difficulty": ex["difficulty"],
                    "tables": ", ".join(ex.get("tables", [])),
                    "sql_patterns": ", ".join(ex.get("sql_patterns", [])),
                }
            )
            ids.append(f"example_{ex['id']}")

    examples_col.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"✅ Embedded {len(documents)} examples into examples_collection")


# ── 3. Smoke Test ─────────────────────────────────────────────────────────────
def smoke_test():
    print("\n🔍 Smoke test — querying: 'top rented movies'")

    schema_results = schema_col.query(
        query_texts=["top rented movies"],
        n_results=3,
    )
    print("\n📌 Relevant tables:")
    for doc in schema_results["documents"][0]:
        print(f"  - {doc.split(chr(10))[0]}")

    example_results = examples_col.query(
        query_texts=["top rented movies"],
        n_results=3,
    )
    print("\n📌 Relevant examples:")
    for doc in example_results["documents"][0]:
        print(f"  - {doc.split(chr(10))[0]}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"💾 ChromaDB will persist to: {CHROMA_PATH}\n")
    embed_schema()
    embed_examples()
    smoke_test()
    print("\n✅ Done. ChromaDB is ready.")
