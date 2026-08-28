---
name: sync-wiki
description: >-
  Synchronize and update the Vesta project GitHub Wiki documentation based on the current codebase state.
  Activate this skill whenever the user asks to update, actualize, sync, or refresh the project wiki documentation.
---

# Sync Project Wiki Skill (`sync-wiki`)

This skill provides step-by-step procedures for the agent to inspect the current Vesta codebase, identify recent modifications across the backend and bot services, and automatically update the corresponding GitHub Wiki pages.

---

## 🎯 Goal & Scope

Ensure the Vesta GitHub Wiki repository (`https://github.com/mezgoodle/Vesta.wiki.git`) accurately reflects the current codebase:
- **Backend Architecture & REST API** (`backend/app/api`, `backend/app/models`, `backend/app/schemas`, `backend/app/services`)
- **Multi-Agent System** (`backend/app/agents`, `backend/app/services/adk_service.py`, `backend/app/services/gemini_tools.py`)
- **Telegram Bot** (`bot/tgbot/handlers`, `bot/tgbot/keyboards`, `bot/tgbot/middlewares`, `bot/tgbot/states`)
- **Integrations & Cloud Services** (Google Workspace, Gemini, Home Assistant, Open-Meteo, GCP Cloud Run & Cloud Scheduler)
- **Setup & Configuration** (`.env.example`, `pyproject.toml`, `alembic.ini`, `Dockerfile`)

---

## 🛠️ Step-by-Step Execution Workflow

### Step 1: Clone or Pull the Latest Wiki Repository

1. Locate a temporary scratch directory for the wiki workspace:
   - Path: `$TEMP_DIR/vesta_wiki` or `<appDataDir>\brain\<conversation-id>\scratch\wiki`
2. Check if the wiki directory exists:
   - If **not cloned yet**:
     ```powershell
     git clone https://github.com/mezgoodle/Vesta.wiki.git <wiki_path>
     ```
   - If **already exists**:
     ```powershell
     cd <wiki_path>
     $originUrl = (git remote get-url origin).Trim()
     if ($originUrl -ne "https://github.com/mezgoodle/Vesta.wiki.git") {
         throw "Invalid wiki remote URL: $originUrl. Expected https://github.com/mezgoodle/Vesta.wiki.git"
     }
     git pull origin master
     ```

---

### Step 2: Codebase Inspection & Change Detection

Inspect the main codebase for recent additions, modifications, or deletions:

1. **Backend Endpoints & API**:
   - Check `backend/app/api/v1/api.py` and `backend/app/api/v1/endpoints/*.py`.
   - Identify new or changed routes, parameters, response schemas, and auth requirements.
2. **AI & Multi-Agent Layer**:
   - Check `backend/app/agents/*.py` for new/updated agents.
   - Check `backend/app/services/gemini_tools.py` for new tools attached to agents.
   - Check `backend/app/services/adk_service.py` and `chat_manager.py` for memory or summarization updates.
3. **Database Models & Migrations**:
   - Check `backend/app/models/*.py` and `backend/migrations/versions/*.py`.
   - Update ER-diagram and schema definitions if tables/columns changed.
4. **Telegram Bot Handlers & Commands**:
   - Check `bot/tgbot/handlers/*.py` and `bot/tgbot/services/setting_commands.py`.
   - Check new middlewares (`bot/tgbot/middlewares/`) and keyboards (`bot/tgbot/keyboards/`).
5. **Configuration & Integrations**:
   - Check `backend/app/core/config.py` and `backend/.env.example`.
   - Check new third-party integrations, GCP services, or Home Assistant features.

---

### Step 3: Update Corresponding Wiki Pages

Modify the relevant `.md` files in `<wiki_path>`:

| Wiki Page | Content Scope | Update When |
| :--- | :--- | :--- |
| **`Home.md`** | Overview, high-level features, repository structure, sitemap | Major new features or architectural changes are introduced |
| **`_Sidebar.md`** | Navigation menu across all pages | New wiki pages are added or titles change |
| **`Architecture.md`** | High-level diagrams, system components, database ERD, request flows | Architecture, database models, or core data flows change |
| **`Multi-Agent-System.md`** | ADK agents, tools closures, memory (`UserFact`), rolling summaries, RAG | Agents, tools, memory, or prompt engineering logic changes |
| **`Telegram-Bot.md`** | Bot commands table, FSM lifecycle, voice STT/TTS pipeline, ACL system | Bot commands, keyboards, FSM states, or audio processing changes |
| **`Backend-API.md`** | REST API endpoints by tag, security headers, Serverless Cron jobs | API endpoints, request/response schemas, or auth headers change |
| **`Integrations.md`** | Google Workspace, Gemini, Home Assistant, Open-Meteo, GCP Cloud Run | External APIs, OAuth flows, or cloud configurations change |
| **`Setup-and-Deployment.md`**| Local setup (`uv`), `.env` variables table, Alembic, Docker, Cloud Run | Dependencies, environment variables, or deploy steps change |

---

### Step 4: Quality & Markdown Verification

1. Ensure all updated files use standard GitHub-Flavored Markdown.
2. Validate Mermaid diagram syntax (````mermaid ... ````).
3. Ensure all links between wiki pages use relative wiki link format (e.g. `[Architecture](Architecture)`).
4. Remove any transient `.metadata.json` or scratch artifacts from `<wiki_path>`.

---

### Step 5: Commit & Push Wiki Changes

1. Navigate to the `<wiki_path>` directory.
2. Check git status and stage only the explicitly reviewed pages changed by this sync:
   ```powershell
   git status
   git add -- <pages_changed_by_this_sync>
   ```
3. Commit with a descriptive conventional commit message:
   ```powershell
   git commit -m "docs(wiki): sync documentation with recent codebase changes"
   ```
4. Validate remote URL and push to the active wiki branch (typically `master` for GitHub Wiki):
   ```powershell
   $originUrl = (git remote get-url origin).Trim()
   if ($originUrl -ne "https://github.com/mezgoodle/Vesta.wiki.git") {
       throw "Invalid wiki remote URL: $originUrl. Expected https://github.com/mezgoodle/Vesta.wiki.git"
   }
   git push origin master
   ```

---

### Step 6: Report Summary

Provide a concise summary to the user:
- List of updated wiki pages.
- Highlight of key sections added or refreshed.
- Clickable link to the live wiki: `https://github.com/mezgoodle/Vesta/wiki`.
