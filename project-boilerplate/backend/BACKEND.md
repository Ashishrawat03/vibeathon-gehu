# ⚙️ BACKEND.md — Complete Backend Architecture & Operations Manual

Ye document tumhare **FastAPI + `uv` + AI Stack (Groq + Gemini + HuggingFace + Supabase)** backend ka complete manual hai. Hackathon shuru hote hi tum ya tumhara AI Coding Agent (Claude Code / Cursor / Windsurf) is manual ko follow karke turant kaam start kar sakte ho.

---

## 1. Complete Backend Folder Structure

```text
project-boilerplate/
├── backend/
│   ├── main.py                  # Core FastAPI app instance, CORS, lifespan & router mounting
│   ├── run.py                   # Entrypoint script jo uvicorn ke through main.py ko run karta hai
│   ├── pyproject.toml           # uv dependencies aur project configuration
│   ├── .python-version          # Python version lock (3.11) for uv
│   ├── .env.example             # Template for all API keys (Groq, Gemini, HF, Supabase)
│   ├── BACKEND.md               # Ye manual (architecture + commands + workflow)
│   ├── app/                     # Modular application package (AI Agent yahan code likhega)
│   │   ├── __init__.py
│   │   ├── core/                # Configs, Pydantic settings, JWT Auth security middleware
│   │   ├── api/
│   │   │   └── routes/          # Alag-alag feature endpoints (auth.py, chat.py, rag.py, etc.)
│   │   ├── services/            # Core business logic & LLM wrappers:
│   │   │                        #   - groq_service.py (fast LPU inference)
│   │   │                        #   - gemini_service.py (multimodal / long-context)
│   │   │                        #   - embedding_service.py (HuggingFace embeddings)
│   │   ├── agents/              # Multi-step AI agents, system prompts & tool-calling workflows
│   │   ├── db/                  # Supabase client & pgvector database queries
│   │   ├── models/              # Database table definitions / ORM models
│   │   ├── schemas/             # Pydantic v2 Request & Response schemas (strict type validation)
│   │   └── utils/               # Helper functions (PDF/text chunking, parsers, formatters)
│   └── tests/                   # Pytest unit & integration tests
├── frontend/
│   └── index.html               # Minimal placeholder HTML (with backend health-check button)
├── AGENT.md                     # AI Coding Assistant instructions (Claude/Cursor master rules)
├── TODO.md                      # Hackathon phased execution & judge-winning checklist
├── .gitignore                   # Prevents .venv, .env, and cache files from going to Git
└── README.md                    # Master guide (AI models, Auth/DB comparison, setup)
```

---

## 2. Backend Kese Kaam Karega? (Request Lifecycle Flow)

Jab frontend ya user koi request bhejta hai, backend me data is flow me travel karta hai:

1. **`run.py` -> `main.py` (Server Entry)**:
   - `run.py` `.env` file load karta hai aur Uvicorn ASGI server start karta hai jo `main:app` ko host karta hai.
   - `main.py` CORS headers lagata hai taaki frontend (`localhost:3000`, `localhost:5173`, ya `index.html`) bina CORS error ke API call kar sake.
2. **Auth Verification (`app/core/security.py`)**:
   - Frontend se user login hone ke baad `Authorization: Bearer <SUPABASE_JWT>` header aata hai.
   - FastAPI dependency (`Depends(get_current_user)`) token verify karti hai aur `user_id` extract karti hai.
3. **Router Layer (`app/api/routes/*.py`)**:
   - Route endpoint request receive karta hai aur `app/schemas/` ke Pydantic model se input validate karta hai.
4. **AI / Service Layer (`app/services/` & `app/agents/`)**:
   - **Fast Query / Chat / Intent Routing** -> **Groq API** (`llama-3.3-70b-versatile` ya `llama-3.1-8b-instant`) ko call karta hai (sub-second response).
   - **PDF / Image / Audio / Complex JSON / Long Context** -> **Google Gemini API** (`gemini-2.5-flash` ya `gemini-2.5-pro`) ko call karta hai.
   - **RAG / Document Search** -> **HuggingFace Embedding Model** (`BAAI/bge-small-en-v1.5`) se text ko vector (384 dims) me convert karke **Supabase `pgvector`** me similarity search karta hai.
5. **Database Layer (`app/db/`)**:
   - User history, metadata, aur embeddings **Supabase PostgreSQL** me save hote hain.
6. **Structured JSON Response**:
   - FastAPI clean Pydantic schema me frontend ko JSON (ya Server-Sent Events stream) return karta hai.

---

## 3. `uv` + `.venv` Setup & Commands Cheat Sheet

Tumhara backend `uv` (extremely fast Rust-based Python package & venv manager) use karta hai.

### Step 1: Backend folder me jao
```bash
cd project-boilerplate/backend
```

### Step 2: `uv` se Virtual Environment (`.venv`) banao
```bash
uv venv
```
*(Ye `backend/.venv` folder create kar dega).*

### Step 3: `.venv` ko Activate karo
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Linux / macOS / Git Bash**:
  ```bash
  source .venv/bin/activate
  ```

### Step 4: Dependencies Install karo (`pyproject.toml` se)
```bash
uv sync
```
*(Agar local HuggingFace embeddings via `sentence-transformers` bhi chahiye, to run karo: `uv sync --extra local-embeddings`)*

### Step 5: `.env` File Setup karo
```bash
cp .env.example .env
```
Ab `.env` file khol kar apni `GROQ_API_KEY`, `GEMINI_API_KEY`, `HF_TOKEN`, aur `SUPABASE_URL` / `SUPABASE_ANON_KEY` daal do.

### Step 6: Server Run karo (`run.py` ke through)
```bash
uv run python run.py
```
*(Ya agar `.venv` already activated hai to seedha `python run.py` bhi chala sakte ho!)*

---

## 4. Useful `uv` Commands (Hackathon ke dauran kaam aayenge)

| Kaam (Task) | Command |
| :--- | :--- |
| Naya package install karna (aur `pyproject.toml` me auto-add karna) | `uv add <package-name>` (e.g., `uv add langchain-groq`) |
| Dev dependency add karna | `uv add --dev pytest` |
| Package remove karna | `uv remove <package-name>` |
| Bina venv manually activate kiye koi script chalana | `uv run python <script.py>` |
| Installed packages ki list dekhna | `uv pip list` |

---

## 5. Server Verify Kaise Karein?

Server start hone ke baad apne browser ya terminal me ye URLs check karo:
- **Root Check**: `http://localhost:8000/`
- **Health & API Keys Check**: `http://localhost:8000/api/health` (Ye batayega ki konsi API keys `.env` me set hain!)
- **Interactive Swagger UI (API Testing)**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
