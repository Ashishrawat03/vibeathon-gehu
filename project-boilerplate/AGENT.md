# 🤖 AGENT.md — Master Instructions for AI Coding Assistants

> **NOTICE TO AI AGENT**: Read this file fully before writing any code. This repo is a Hackathon boilerplate (6-hour build, ~30 prompts total, team of 4, I own backend). Goal: a **working, impressive, demo-ready AI app**, not a perfect one.

---

## 🚨 PROMPT-BUDGET RULES (HIGHEST PRIORITY)

We have very few prompts. Every response must deliver maximum working output.

1. **NEVER ask clarifying questions.** Make the most reasonable assumption, list assumptions (max 3 lines) at the end, and continue.
2. **Build vertical slices**: schema + service + route + frontend hook for a feature in ONE response.
3. **No long explanations.** Reply format only: `Files changed` -> `How to run/test (1-2 commands)` -> `Assumptions`.
4. **Self-verify before replying**: check imports, run a smoke test (`uv run python -c ...` or curl). Fix your own errors in the same turn.
5. **Do NOT refactor, rename, or touch working code** unless asked. Do NOT add features outside `TODO.md`.
6. **Tick `[x]` finished items in `TODO.md` every turn.** If I say "continue", do the next 2-3 unchecked items.
7. **Reuse existing code**: `app/services/llm_service.py` (`generate`, `generate_json`, Groq<->Gemini fallback), `app/core/config.py`, `app/schemas/common.py` (`AIResponse` + `AIMeta`). Never re-implement them.
8. **Every AI endpoint returns `AIResponse`** (data + meta: provider, model_used, latency_ms, fallback_used, confidence_score, citations).
9. **Stub first, polish later.** If a feature is risky, return realistic mock data behind the same API contract so frontend is never blocked.
10. **If an API key is missing or a provider fails**, degrade gracefully (fallback / mock) — the demo must never crash.

---

## 🧭 STEP 1: FIRST ACTION — REWRITE `TODO.md`

When I give the problem statement, do NOT dump code. First, in ONE response:
1. Rewrite `TODO.md` as a time-boxed plan for THIS problem: max **4 must-have features + 2 wow features**.
2. At the top of `TODO.md`, write the **API contract** (method, path, request JSON, response JSON) so frontend teammates can start immediately.
3. Create Pydantic v2 schemas, SQLite tables, and all route files with working stub logic; register routers in `main.py`.

Then implement item by item. Phases:
- **Phase 1**: Schemas, DB, route stubs, API contract (first 30 min)
- **Phase 2**: Core MVP flow working end-to-end
- **Phase 3**: AI depth (hybrid search, agent logic, multimodal, routing)
- **Phase 4**: Polish: `/api/v1/demo/seed`, telemetry fields, Swagger tags + examples, error handling

---

## 🛠️ STEP 2: DEFAULT STACK CHOICES (don't deliberate, just use these)

| Need | Use | Why |
| :--- | :--- | :--- |
| Packages / env | `uv` only (`uv add`, `uv run python run.py`), venv in `backend/.venv` | Fast, no pip/poetry |
| Database | **SQLite** (`sqlite3` or SQLModel), file `backend/data/app.db` | Zero setup, no network |
| Keyword search | **SQLite FTS5** (`bm25()`) | Built-in, fast |
| Semantic search | HF embeddings (`BAAI/bge-small-en-v1.5`, 384-dim) stored as float32 BLOB in SQLite; **cosine via numpy** in memory | Fine up to ~50k chunks, no vector DB |
| Hybrid search | **FTS5 top-20 + vector top-20 merged with Reciprocal Rank Fusion** (`score = sum(1/(60+rank))`), return top 5 with citations | Beats either alone |
| Fast chat / routing / classification | Groq `llama-3.3-70b-versatile` / `llama-3.1-8b-instant` | <500ms |
| PDF / image / audio / long context / strict JSON | Gemini `gemini-2.5-flash` (`google-genai` SDK) | Multimodal |
| Fallback | Built into `llm_service.generate` (Groq <-> Gemini) | Demo never dies |
| Streaming (if chat UI) | FastAPI `StreamingResponse` with SSE | Feels instant |
| Caching | `functools.lru_cache` / in-memory dict for repeated LLM/embedding calls | Saves rate limits |
| Auth | **None by default.** Add simple JWT/session only if the problem requires users | Saves prompts |
| Supabase | **Optional**, only if multi-user cloud data is truly required | Setup costs prompts |
| Frontend | Single `frontend/index.html`, vanilla JS + `fetch`, dark UI, loading states, error toasts, telemetry badge | No build step |
| Config | `app/core/config.py` (`get_settings()`), never `os.getenv` scattered | Clean |

### Hybrid search implementation spec (build in ONE prompt when needed)
- `app/services/embedding_service.py`: `embed_texts(list[str]) -> list[list[float]]` via HF Inference API (`HF_TOKEN`), batch calls, `lru_cache` on queries. Fallback to local `sentence-transformers` if `USE_LOCAL_EMBEDDINGS=true`.
- `app/services/search_service.py`: `ingest(docs)`, `hybrid_search(query, k=5)`. Tables: `documents(id, text, metadata_json, embedding BLOB)` + FTS5 virtual table `documents_fts`. Embed at ingest time, never at query time for docs.
- Response includes `citations` (doc id, snippet, keyword rank, vector rank, fused score).

---

## 🧱 STEP 3: CODE RULES

1. **Keep `backend/run.py` and `backend/main.py` contract.** `run.py` launches `main:app`. `main.py` stays thin: app, CORS, health, `include_router(...)`. Handlers go in `app/api/routes/*.py`.
2. **Env keys** via `Settings`: `GROQ_API_KEY`, `GEMINI_API_KEY`, `HF_TOKEN` (+ model names).
3. **Every endpoint**: `async def`, Pydantic `response_model`, docstring, tags, example payload (so `/docs` looks professional to judges).
4. **Errors**: `HTTPException` with structured JSON. Never leak raw stack traces. LLM total failure -> 503 with friendly message.
5. **Non-blocking I/O**: `httpx.AsyncClient` / async SDKs. Wrap blocking calls (sqlite3, HF sync client) in `asyncio.to_thread`.
6. **LLM output as JSON**: use `generate_json`, validate with Pydantic, retry once on parse failure.
7. **Prompts for LLMs** live in `app/agents/prompts.py` as constants, not inline strings.

---

## 🏆 STEP 4: WINNING FEATURES (build in this order if time permits)

1. **Telemetry badge**: frontend shows model, latency, confidence, sources from `meta`.
2. **Demo seed**: `POST /api/v1/demo/seed` loads realistic sample data so the demo runs in 10 seconds.
3. **Explainability**: return a short `reasoning_trace` (which steps/tools/models ran).
4. **Smart routing**: simple tasks -> Groq 8b, complex -> Groq 70b / Gemini; show it in meta.

---

## ✅ DEFINITION OF DONE (every turn)
- Server starts with `uv run python run.py`, `/docs` loads
- New endpoints smoke-tested with a real request
- `TODO.md` updated
- Reply uses the short format from the Prompt-Budget Rules
