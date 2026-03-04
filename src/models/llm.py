import re
from langchain_ollama import OllamaLLM
from src.rag.retriever import retrieve_context

# ── Models ────────────────────────────────────────────────────────────────────
QWEN = "qwen2.5-coder"
CODELLAMA = "codellama"


# ── Prompt Template ───────────────────────────────────────────────────────────
PROMPT_TEMPLATE = """\
    You are an expert PostgreSQL assistant. Your job is to write a single, valid \
    PostgreSQL query that answers the user's question.
    
    Rules:
    - Only output the SQL query. No explanation, no markdown, no comments.
    - Use only the tables and columns provided in the schema below to you.
    - Use JOINs wherever necessary based on foreign key relationships.
    - Always use table aliases for clarity and avoiding ambiguity.
    - Ensure the SQL is syntactically correct and can be executed without modification.
    - End the query with a semicolon.
    
    {context}
    
    ### Question:
    {question}
    
    ### SQL:
"""
# ── SQL Extractor ─────────────────────────────────────────────────────────────
def extract_sql(raw: str) -> str:
    """
    Strip markdown code fences and whitespace from LLM output,
    returning only the raw SQL string, ready for execution.
    """
    # Remove ```sql ... ``` or ``` ... ```
    cleaned = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()
    return cleaned


# ── Core Generation Function ──────────────────────────────────────────────────
def generate_sql(
    question: str, model: str = QWEN, n_schema: int = 5, n_examples: int = 3
) -> dict:
    """
    Given a natural language question:
    1. Retrieve relevant schema + examples from ChromaDB
    2. Build a prompt
    3. Call the specified Ollama model
    4. Extract and return the SQL

    Returns a dict with:
        - question: original question
        - model: model used
        - context: retrieved context
        - prompt: full prompt sent to LLM
        - raw_response: raw LLM output
        - sql: extracted SQL query
    """

    # 1. Retrieve context
    context = retrieve_context(question, n_schema=n_schema, n_examples=n_examples)

    # 2. Build prompt
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)

    # 3. Call LLM
    llm = OllamaLLM(model=model, temperature=0)
    raw_response = llm.invoke(prompt)

    # 4. Extract SQL
    sql = extract_sql(raw_response)

    return {
        "question": question,
        "model": model,
        "context": context,
        "prompt": prompt,
        "raw_response": raw_response,
        "sql": sql,
    }


# ── Compare Both Models ───────────────────────────────────────────────────────
def compare_models(question: str) -> dict:
    """
    Run the same question through both Qwen2.5-Coder and CodeLlama
    and return both results for comparison.
    """
    print(f"\n🤖 Running: {QWEN}")
    qwen_result = generate_sql(question, model=QWEN)

    print(f"\n🤖 Running: {CODELLAMA}")
    codellama_result = generate_sql(question, model=CODELLAMA)

    return {
        "question": question,
        QWEN: qwen_result["sql"],
        CODELLAMA: codellama_result["sql"],
    }

