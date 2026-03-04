# Text-to-SQL Chatbot 🤖

Ask questions about the **dvdrental** database in plain English — the chatbot will generate and run the SQL for you.

## Example Questions

- *Who are the top 5 customers by total payments?*
- *Which films have never been rented?*
- *Show month-over-month revenue growth rate.*
- *Which actors have appeared in the most Action films?*

## Models

Use the ⚙️ settings panel to switch between:
- `qwen2.5-coder` — faster (avg 2.3s), 100% execution success
- `codellama` — more accurate (95% match), slightly slower (avg 2.8s)

## Requirements

Make sure **Ollama** is running locally with the required models pulled:
```bash
ollama pull qwen2.5-coder
ollama pull codellama
ollama pull nomic-embed-text
```
