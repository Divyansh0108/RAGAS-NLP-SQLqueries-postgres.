"""
Text-to-SQL Chatbot — Entry Point

Usage:
    Start the chatbot UI:
        uv run chainlit run src/ui/app.py --port 8000

    Re-embed schema and examples (after DB changes):
        uv run python scripts/embed_schema_and_examples.py

    Validate NL-SQL examples against the DB:
        uv run python scripts/validate_examples.py

    Run model evaluation (Qwen vs CodeLlama):
        uv run python src/eval/evaluator.py
"""
