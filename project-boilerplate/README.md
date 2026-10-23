# 🚀 AI Hackathon Project Boilerplate (`uv` + FastAPI + Groq + Gemini + HuggingFace + Supabase)

Ye boilerplate specially **AI Hackathons** ke liye design kiya gaya hai taaki tumhe zero-se folder setup, environment management, ya architecture sochne me time waste na karna pade. Is repo ko seedha GitHub par push karo, kisi bhi hackathon me clone karo, aur apne AI Coding Agent (**Claude Code / Cursor / Windsurf**) ko prompt dekar turant advanced project build karna start kar do!

---

## 📂 1. Project Folder Structure

```text
project-boilerplate/
├── backend/                     # Python FastAPI Backend (managed via uv + .venv)
│   ├── main.py                  # Core FastAPI server setup, CORS, /api/health & router mounts
│   ├── run.py                   # Runner script jo main.py ko Uvicorn ke sath launch karta hai
│   ├── pyproject.toml           # uv package configuration & dependencies
│   ├── .python-version          # Python 3.11 version pin for uv
│   ├── .env.example             # API Keys template (Groq, Gemini, HuggingFace, Supabase)
│   ├── BACKEND.md               # Complete Backend Manual (flow, architecture, uv commands)
│   ├── app/                     # Modular packages jahan AI agent feature code likhega
│   │   ├── api/routes/          # API endpoints (auth, chat, rag, agents, etc.)
│   │   ├── core/                # Configs, settings & JWT Auth middleware
│   │   ├── services/            # Groq, Gemini, aur HuggingFace Embedding services
│   │   ├── agents/              # Multi-step AI agent workflows & prompts
│   │   ├── db/                  # Supabase PostgreSQL + pgvector client
│   │   ├── models/              # DB models
│   │   ├── schemas/             # Pydantic v2 Request/Response validation models
│   │   └── utils/               # Helper functions (PDF/text chunking, parsers)
│   └── tests/                   # Pytest folder
├── frontend/
│   └── index.html               # Starter HTML file (includes a live Backend Health Test button)
├── AGENT.md                     # Master instructions for Claude / Cursor AI coding assistant
├── TODO.md                      # Phased roadmap & Hackathon Judge-Winning checklist
├── .gitignore                   # Ignores .venv, .env, __pycache__ for clean Git uploads
└── README.md                    # Master documentation (Models, Auth, DB & Quickstart)
```

---

## 🧠 2. AI Models Guide — Kya Hai, Kyu Hai, Aur Kon Sa Model Kab Use Karna Hai?

Hackathon me ek hi model har jagah use karne se ya to app slow ho jata hai ya rate-limit hit ho jata hai. Is boilerplate me **3-Pillar Hybrid AI Stack** configured hai:

### A. Groq Models (Ultra-Fast LPU Inference ⚡)
- **Kya hai**: Groq apne custom LPU (Language Processing Unit) hardware par open-source models run karta hai jo **300 se 800+ tokens/second** ki extreme speed deta hai.
- **Kyu use karein**: Hackathon demo me jab judge button click kare aur jawab **0.3 second** me screen par aa jaye, to real-time experience kamaal ka lagta hai.
- **Kon sa model kab use karein**:
  1. **`llama-3.3-70b-versatile` (Default Primary)**: Main chat agent, tool-calling, summarization, aur high-quality responses ke liye best balance of intelligence + speed.
  2. **`llama-3.1-8b-instant` (Ultra-Fast Router/Guardrail)**: User ka intent classify karne, query rewrite karne, ya quick guardrails check karne ke liye (~100ms latency).
  3. **`deepseek-r1-distill-llama-70b` (Fast Reasoning)**: Step-by-step logic, math, ya code generation/debugging tasks ke liye.

### B. Google Gemini Models (Multimodal + 1M+ Context Window 🌐)
- **Kya hai**: Google ke native multimodal models jo text, images, PDFs, audio, aur video ek sath samajh sakte hain aur **1 Million+ tokens** ka huge context window dete hain.
- **Kyu use karein**: Groq sirf text/fast inference ke liye hai, lekin jab user **PDF upload kare, screenshot/image de, audio note bheje, ya 100-page document analyze karna ho**, tab Gemini unbeatable hai. Plus Gemini ka `response_schema` (Structured JSON Output) 100% strict JSON deta hai.
- **Kon sa model kab use karein**:
  1. **`gemini-2.5-flash` (Default Multimodal & Structured Output)**: Fast, cheap/free-tier friendly, best for PDF/image extraction, vision tasks, aur long-context RAG synthesis.
  2. **`gemini-2.5-pro` (Deep Complex Reasoning & Coding)**: Jab bohot heavy system design, complex legal/medical/financial analysis, ya multi-document synthesis karna ho.

### C. HuggingFace Models (Embeddings & Semantic Search 🔍)
- **Kya hai**: Text chunks ko numerical vectors (arrays of floats) me convert karne wale models taaki hum meaning-based search (RAG) kar sakein.
- **Kyu use karein**: OpenAI embeddings ke paise lagte hain, jabki HuggingFace ke top embedding models **100% Free** hain—inhain tum `huggingface-hub` Inference API se bina GPU ke call kar sakte ho ya `sentence-transformers` se local CPU par chala sakte ho.
- **Kon sa model kab use karein**:
  1. **`BAAI/bge-small-en-v1.5` (Recommended Default — 384 dimensions)**: MTEB leaderboard par apne size me top-performing English embedding model. Lightweight hai, super fast hai, aur vector DB me kam memory leta hai.
  2. **`sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)**: Classic ultra-fast lightweight embedding model for quick prototypes.
  3. **`BAAI/bge-m3` (1024 dimensions — Multilingual)**: Agar tumhara hackathon project **Hindi + Hinglish + English** (multilingual documentos) par kaam karta hai, to `bge-m3` use karo.

---

## 🔐 3. Auth & Database Guide — Supabase vs Firebase (Kya Use Karna Chahiye?)

Tumne pucha tha ki **Auth aur Database ke liye kya use karna chahiye — Supabase ya Firebase?**

### 🏆 Clear Recommendation for AI Python/FastAPI Hackathons: **Supabase**

| Feature | **Supabase (Recommended 🥇)** | **Firebase** |
| :--- | :--- | :--- |
| **Database Type** | **PostgreSQL (Relational SQL)** — Structured tables, joins, aur analytics ke liye best | **Firestore (NoSQL Document DB)** — Nested documents, complex queries aur joins me mushkil |
| **Vector DB for AI (RAG)** | **Built-in `pgvector`!** Alag se Pinecone/Chroma setup nahi karna padta; same DB me users + embeddings dono rehte hain | Native vector search limited hai; aksar alag vector DB (Pinecone/Qdrant) jodna padta hai |
| **Auth Integration** | **Supabase Auth** (Email, Google, GitHub OAuth, Magic Links) — Standard JWT token deta hai jo FastAPI me 10 lines me verify ho jata hai | **Firebase Auth** — Achha hai, par backend par `firebase-admin` SDK + service account JSON manage karna padta hai |
| **Python / FastAPI DX** | Official `supabase` Python client + standard SQL (`asyncpg` / `SQLAlchemy`) support | Python me Firestore queries likhna SQL ke mukable thoda verbose hota hai |

### 💡 Final Decision Rule:
1. **Default Choice -> Use Supabase (Auth + PostgreSQL + `pgvector` + Storage)**:
   - Frontend par `@supabase/supabase-js` se Google/Email login karwao.
   - Frontend har API call me `Authorization: Bearer <access_token>` FastAPI ko bhejega.
   - FastAPI us JWT ko verify karega aur usi Supabase PostgreSQL database me normal tables + `pgvector` embeddings dono store karega!
2. **Kab Firebase use karein?**
   - Sirf tab jab tumhara frontend teammate Firebase Auth + Firestore me pehle se expert ho aur project me relational SQL ya vector search ki zaroorat kam ho.

---

## ⚡ 4. Quickstart — Server Ko Kaise Run Karein?

### Step 1: Backend folder me jao aur `uv` se `.venv` banao
```bash
cd backend
uv venv
```

### Step 2: Virtual Environment Activate karo
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Linux / macOS / Git Bash**:
  ```bash
  source .venv/bin/activate
  ```

### Step 3: Dependencies Install karo
```bash
uv sync
```

### Step 4: `.env` File Configure karo
```bash
cp .env.example .env
```
*(Ab `.env` me apni Groq, Gemini, HuggingFace, aur Supabase keys paste kar do).*

### Step 5: `run.py` se FastAPI Server Chalao!
```bash
uv run python run.py
```
Ab browser me kholo:
- **Swagger UI (Interactive API Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **Frontend Test**: `frontend/index.html` ko browser me double-click karke kholo aur **"Test FastAPI Backend Connection"** button dabao!

---

## 🏆 5. Hackathon Me AI Agent (Claude / Cursor) Se Advanced Project Kaise Banwayein?

Jab hackathon me problem statement mil jaye, apne AI Coding Assistant (Claude Code / Cursor) me ye prompt copy-paste karo:

> **Prompt to give your AI Agent at the Hackathon:**
> *"Read `AGENT.md`, `README.md`, and `backend/BACKEND.md` first. Hum ek hackathon me hain aur hamara problem statement ye hai: [PASTE PROBLEM STATEMENT HERE]. Sabse pehle `TODO.md` ko update karke ek advanced, judge-winning Todo List banao jisme MVP endpoints, Groq + Gemini hybrid routing, HuggingFace + Supabase pgvector RAG, fallback handling, aur एक `/api/v1/demo/seed` endpoint ho. Todo list banane ke baad Phase 1 se step-by-step backend implement karna start karo using `uv`."*
