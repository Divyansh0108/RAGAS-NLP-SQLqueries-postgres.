import chainlit as cl

from src.db.executor import execute_sql, format_results
from src.models.llm import CODELLAMA, QWEN, generate_sql

# ── Settings ──────────────────────────────────────────────────────────────────
MODELS = [QWEN, CODELLAMA]


@cl.on_chat_start
async def on_chat_start():
    # Default model
    cl.user_session.set("model", QWEN)

    # Model selector
    settings = await cl.ChatSettings(
        [
            cl.input_widget.Select(
                id="model",
                label="SQL Model",
                values=MODELS,
                initial_value=QWEN,
            )
        ]
    ).send()

    await cl.Message(
        content=(
            "👋 Welcome to the **Text-to-SQL Chatbot**!\n\n"
            "Ask me any question about the **dvdrental** database in plain English.\n\n"
            f"🤖 Current model: `{QWEN}`\n"
            "You can switch models using the ⚙️ settings above."
        )
    ).send()


@cl.on_settings_update
async def on_settings_update(settings):
    model = settings["model"]
    cl.user_session.set("model", model)
    await cl.Message(content=f"✅ Model switched to `{model}`").send()


@cl.on_message
async def on_message(message: cl.Message):
    question = message.content.strip()
    model = cl.user_session.get("model", QWEN)

    # ── Step 1: Thinking ──────────────────────────────────────────────────────
    async with cl.Step(name="🔍 Retrieving context + generating SQL") as step:
        step.input = question

        # Generate SQL
        result = generate_sql(question, model=model)
        sql = result["sql"]
        step.output = f"```sql\n{sql}\n```"

    # ── Step 2: Execute SQL ───────────────────────────────────────────────────
    async with cl.Step(name="⚙️ Executing SQL against PostgreSQL") as step:
        step.input = sql
        execution = execute_sql(sql)
        step.output = "Success" if execution["success"] else execution["error"]

    # ── Step 3: Display Results ───────────────────────────────────────────────
    formatted = format_results(execution)

    await cl.Message(
        content=(
            f"### 🧠 Generated SQL\n"
            f"```sql\n{sql}\n```\n\n"
            f"### 📊 Results\n"
            f"```\n{formatted}\n```\n\n"
            f"*Model: `{model}`*"
        )
    ).send()
