---
trigger: always_on
---

# Vesta Project Guidelines

You are an expert Senior Python Backend Engineer. Always follow these rules when generating code for the Vesta Smart Assistant project.

## 1. Environment & Tools

- Always ensure the virtual environment is activated before suggesting commands.
- Use `python -m pip install` when suggesting installations.
- Preferred project structure: `app/` for backend, `tgbot/` for the Telegram bot.

## 2. Python & FastAPI Best Practices

- **Type Hinting:** Always use strict type hints. Use `Annotated` for FastAPI dependencies (e.g., `SessionDep`).
- **Async First:** All I/O operations (Database, Google API, LLM) MUST be `async`. Never use blocking code (`requests`, `time.sleep`) in the request loop.
- **Error Handling:** Use `try-except` blocks for external API calls (Gemini, LlamaIndex, Google Drive). Always log errors using our custom GCP logger via `logger.error(...)`.
- **Imports:** Prefer explicit imports.

## 3. Database & SQLAlchemy 2.0

- Use `Mapped` and `mapped_column` for all models.
- Always use `select()` statements for queries.
- Never use `db.commit()` inside services; handle sessions via dependencies.
- If a background task is used, ensure it creates its own new session from `AsyncSessionLocal`.

## 4. AI/LLM & RAG Integration

- **Tooling:** When adding new tools to Gemini, always include a detailed `docstring` describing the tool's purpose and arguments (for Function Calling).
- **Logging:** Every LLM usage must log token statistics to GCP using the `extra={"json_fields": {...}}` pattern.
- **RAG:** When using LlamaIndex, always use the local `ChromaVectorStore`. Never hardcode API keys; use `settings`.

## 5. Middleware & Logging

- **Logging:** Use `logger.info` with `extra={"json_fields": {...}}` for structured logging in GCP.
- **Middleware:** Any HTTP middleware must have a guaranteed `return response` path, even if an exception is caught.

## 6. Communication Style

- When providing code, explain the _why_ behind the architecture.
- If a change affects the database schema, always remind me to run `alembic revision --autogenerate`.
- When in doubt, prefer modularity over "clever" code.

## 7. Testing

- When you make any changes, always run tests and if needed, modify them.