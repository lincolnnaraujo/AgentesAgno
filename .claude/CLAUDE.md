# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

POC/examples repository demonstrating AI agents built with the **Agno** framework (target version 2.2.0). Each `agent_*.py` / `playground_*.py` file is a standalone script — there is no shared application entrypoint or package structure.

## Running Agents

Each script is self-contained. Activate the virtualenv and run directly:

```bash
source .venv/Scripts/activate   # Windows Git Bash
python agent_agno_gemini.py     # simple Gemini + Tavily search
python agent_agno_telegram.py   # Telegram bot (long-running)
python agent_slackblt_agno.py   # Slack bot (long-running, Socket Mode)
python agent_git_developer.py   # GitHub automation (clone, PR, etc.)
python agent_rag_pdf.py         # RAG over PDFs with ChromaDB
python agent_financeiro_deepseek.py   # DeepSeek + YFinance
python agent_researcher_deepseek.py   # DeepSeek + Tavily
```

The playground scripts (`playground_agent_agno_gemini.py`) start a local web UI via `AgentOS.serve()` on uvicorn with hot-reload.

## Environment Variables

All scripts load a `.env` file via `python-dotenv`. Required keys vary per script:

| Variable | Used by |
|---|---|
| `GEMINI_API_KEY` | All Gemini-based agents (alternative to Vertex AI) |
| `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` | Gemini via Vertex AI |
| `TAVILY_API_KEY` | Agents with web search |
| `TELEGRAM_TOKEN` + `TELEGRAM_CHAT_ID` | `agent_agno_telegram.py` |
| `SLACK_BOT_TOKEN` + `SLACK_APP_TOKEN` | `agent_slackblt_agno.py` |
| `GITHUB_TOKEN` | `agent_git_developer.py` |
| `DEEPSEEK_API_KEY` | DeepSeek-based agents |

## Architecture Patterns

- **LLM providers**: `agno.models.google.Gemini` (API key or Vertex AI) and `agno.models.deepseek.DeepSeek`.
- **Tools**: Agno built-in tools (`TavilyTools`, `YFinanceTools`, `TelegramTools`) plus custom tools in `customTools/` extending `agno.tools.Toolkit`.
- **Personas**: XML files in `personas/` define agent description + instructions, loaded at runtime (used by the Slack agent).
- **Knowledge/RAG**: `agno.knowledge.Knowledge` + `agno.vectordb.chroma.ChromaDb` with persistent storage in `tmp/chromadb/`.
- **Session storage**: `agno.db.sqlite.SqliteDb` writing to `tmp/data.db` for conversation history.
- **Utility functions**: `functions/` directory (e.g., string sanitization for Telegram Markdown).

### Creating Custom Tools

Custom tools extend `agno.tools.Toolkit`. See `customTools/PokemonApiTools.py` for the pattern: define standalone functions, then wrap them in a `Toolkit` subclass.

## Runtime Artifacts

The `tmp/` directory is gitignored and holds ephemeral data:
- `tmp/data.db` — SQLite conversation history
- `tmp/chromadb/` — ChromaDB vector store

## Code Conventions

- **Python version**: 3.10+ (repo uses `.venv` with Python 3.13)
- **Type hints**: Use modern union syntax (`X | None`, not `Optional[X]`)
- **Formatting**: 4 spaces, double quotes, max 100 chars per line (Black/Ruff)
- **Commits**: Conventional Commits in Portuguese — `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`
- **Dependencies**: managed via pip in `.venv` (no `pyproject.toml` at root yet)
- **Linting**: Ruff / Black
