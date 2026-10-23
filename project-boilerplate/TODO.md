# 🏆 TODO.md — Hackathon Execution & Judge-Winning Roadmap

> **Instruction for AI Agent (Claude / Cursor)**: Jab project ka exact topic bata diya jaye, tab is `TODO.md` ko project ke specific features ke hisaab se customize karo aur har step complete hone par `[x]` mark karte jao.

---

## Phase 1: Setup & Foundation (First 15–30 Mins)
- [x] Folder structure setup (`backend/`, `frontend/`, `main.py`, `run.py`, `BACKEND.md`, `AGENT.md`)
- [ ] Run `cd backend && uv venv && uv sync` to initialize `.venv`
- [ ] Copy `backend/.env.example` to `backend/.env` and fill in API keys (Groq, Gemini, HuggingFace, Supabase)
- [ ] Verify server runs cleanly via `uv run python run.py` and check `http://localhost:8000/api/health`
- [ ] Create Supabase project, enable `vector` extension (`CREATE EXTENSION IF NOT EXISTS vector;`), and configure Auth

## Phase 2: Core Backend Architecture (AI Agent Tasks)
- [ ] **Config & Security (`app/core/`)**:
  - [ ] Create `app/core/config.py` using `pydantic-settings` to validate all `.env` variables
  - [ ] Create `app/core/security.py` to verify Supabase JWT tokens from `Authorization: Bearer <token>`
- [ ] **AI Service Wrappers (`app/services/`)**:
  - [ ] Create `app/services/groq_service.py` (ultra-fast chat, classification, & JSON extraction with `llama-3.3-70b-versatile`)
  - [ ] Create `app/services/gemini_service.py` (multimodal file/image/PDF analysis & long-context reasoning with `gemini-2.5-flash`)
  - [ ] Create `app/services/embedding_service.py` (HuggingFace `BAAI/bge-small-en-v1.5` embeddings for RAG)
  - [ ] Add **Automatic LLM Fallback** (Groq <-> Gemini) so live demos never fail on API rate limits
- [ ] **Database & Vector Store (`app/db/`)**:
  - [ ] Create `app/db/supabase_client.py` for CRUD + `pgvector` similarity search RPC calls

## Phase 3: Hackathon Problem-Specific MVP Endpoints
- [ ] Define Pydantic v2 request/response schemas in `app/schemas/`
- [ ] Build primary feature routers in `app/api/routes/` and mount them in `main.py`
- [ ] Connect frontend UI to FastAPI endpoints

## Phase 4: Judge-Winning "X-Factor" Features (How We Win 1st Place 🥇)
- [ ] **Smart Hybrid Model Router**: Show judges how simple tasks route to Groq (<400ms latency) while multimodal/complex tasks route to Gemini 2.5.
- [ ] **Explainable AI Metadata in Every Response**: Return `latency_ms`, `model_used`, `confidence_score`, and `citations` so the frontend can display a live "AI Telemetry / Transparency Badge".
- [ ] **One-Click Demo Seeder (`/api/v1/demo/seed`)**: Pre-load realistic sample data so the 3-minute pitch demo starts immediately with rich data.
- [ ] **Swagger `/docs` Polish**: Add clean tags, summaries, and example payloads to all FastAPI routes so technical judges inspecting `/docs` are impressed.
