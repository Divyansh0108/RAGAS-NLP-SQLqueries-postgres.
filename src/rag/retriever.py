from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
CHROMA_PATH = ROOT / "data" / "chroma_db"

# ── Embedding Function ────────────────────────────────────────────────────────
embedding_fn = OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text",
)

# ── ChromaDB Client ───────────────────────────────────────────────────────────
client = chromadb.PersistentClient(path=str(CHROMA_PATH))

schema_col = client.get_or_create_collection(
    name="schema_collection",
    embedding_function=embedding_fn,
)

examples_col = client.get_or_create_collection(
    name="examples_collection",
    embedding_function=embedding_fn,
)

# ── Retriever ─────────────────────────────────────────────────────────────────
def retrieve_context(question: str, n_schema: int = 5, n_examples: int = 3) -> str:
    """
    Given a natural language question, retrieve relevant schema tables
    and NL-SQL examples from ChromaDB and return a combined context string.
    """

    # 1. Retrieve relevant tables
    schema_results = schema_col.query(
        query_texts=[question],
        n_results=n_schema,
    )
    schema_docs = schema_results["documents"][0]

    # 2. Retrieve relevant examples
    example_results = examples_col.query(
        query_texts=[question],
        n_results=n_examples,
    )
    example_docs = example_results["documents"][0]

    # 3. Build context string
    context = "### Relevant Tables:\n"
    for doc in schema_docs:
        context += f"{doc}\n\n"

    context += "### Relevant Examples:\n"
    for doc in example_docs:
        context += f"{doc}\n\n"

    return context.strip()