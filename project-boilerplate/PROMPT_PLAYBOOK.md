# 🎯 PROMPT_PLAYBOOK.md — 30 Prompts Me Hackathon Jeetne Ka Plan

Rule #1: **Prompt = bullet, code = bullet ka output.** Har prompt se max kaam nikalwao. Bug fix, planning, UI, pitch jaise kaam FREE platforms par karo, apne 30 coding prompts par nahi.

---

## A. Aaj Raat Ki Prep (Hackathon se pehle — prompts consume nahi hote)

- [ ] `cd backend && uv sync` chalao, error aaye to abhi fix karo
- [ ] `.env` banao, saari keys daalo: Groq, Gemini, HF token (Supabase tabhi jab zaroorat ho)
- [ ] Test: `uv run python -c "import asyncio; from app.services.llm_service import generate; print(asyncio.run(generate('Say hi in 5 words')))"`
      -> Groq chalta hai ya nahi, aur Groq key galat karke fallback Gemini par jaata hai ya nahi, dono check karo
- [ ] `uv run python run.py` -> `/docs` aur `/api/health` khulna chahiye
- [ ] GitHub par push karo (`.env` ignore hai, check kar lo). Venue Wi-Fi bharosemand nahi hota, laptop par bhi ready rakho
- [ ] Antigravity login, internet, charger, hotspot ready
- [ ] Hackathon ke rules padho: pre-written boilerplate allowed hai ya nahi

---

## B. AGENT.md Me Ye Block Paste Karo (Prompt-Saver Rules)

```
## PROMPT-BUDGET RULES (HIGHEST PRIORITY)
We have only ~30 prompts total. Every prompt must produce maximum working output.
1. NEVER ask clarifying questions. Make the most reasonable assumption, list assumptions in 3 lines at the end, and continue.
2. Build VERTICAL SLICES: schema + service + route + frontend hook for one feature in a single response.
3. No long explanations. Reply format: files changed (list) -> how to run/test (1-2 commands) -> assumptions. Nothing else.
4. After writing code, self-check imports and run a smoke test (uv run python -c ... or curl /api/health) before replying. Fix your own errors before ending the turn.
5. Do NOT refactor, rename, or touch working code unless asked. Do NOT add features not in TODO.md.
6. Tick finished items in TODO.md ([x]) at the end of every turn. "Continue" means: do the next 2-3 unchecked items.
7. Reuse existing helpers: app/services/llm_service.py (generate, generate_json with Groq<->Gemini fallback), app/core/config.py, app/schemas/common.py (AIResponse with meta). Every AI endpoint returns AIResponse.
8. DB DEFAULT = SQLite (or in-memory) for speed. Use Supabase/pgvector ONLY if the problem needs multi-user auth or large-scale vector search. No auth unless the problem requires it.
9. For RAG at hackathon scale, use in-memory cosine similarity (numpy) over HF embeddings unless told otherwise.
10. Frontend = single frontend/index.html (vanilla JS + fetch, clean dark UI, loading states, error toasts, telemetry badge showing model/latency).
```

Note: pehle wale AGENT.md me Supabase + JWT mandatory hai. 6 ghante aur 30 prompts me wo 4-6 prompts khaa jaata hai. Rule 8 isi liye hai.

---

## C. 30-Prompt Budget

| Prompts | Kaam |
|---|---|
| 1 | **Kickoff**: problem statement + plan + TODO.md + schemas + saare route stubs |
| 2-4 | Core feature slices (1 prompt = 1 end-to-end feature) |
| 5-6 | AI logic: RAG / agent / multimodal (Gemini for files) |
| 7 | Frontend connect (ya frontend teammate apne tool se kare) |
| 8 | Demo seed endpoint + telemetry badge |
| 9 | Error handling + Swagger polish + README |
| 10-22 | **Bug-fix reserve** (13 prompts) |
| 23-26 | Polish / ek extra "wow" feature |
| 27-30 | **Emergency reserve, kabhi mat kharch karo jab tak final hour na ho** |

---

## D. Copy-Paste Prompts

**Prompt 1 — Kickoff**
```
Read AGENT.md, README.md, backend/BACKEND.md and PROMPT_PLAYBOOK.md first. Problem statement: [PASTE FULL TEXT]. Team: 4 people, 6 hours, I own backend.
Do in ONE response: (1) rewrite TODO.md as a time-boxed plan for THIS problem with only must-have features (max 4) + 2 wow features, (2) create Pydantic schemas, DB models/tables (SQLite), (3) create all route files with working stub logic and register them in main.py, (4) list the exact API contract (method, path, request, response JSON) at the top of TODO.md so frontend teammates can start now. No questions, assume and continue.
```

**Prompt 2-4 — Slice**
```
Implement TODO.md items [X, Y] fully: service logic using llm_service.generate/generate_json, route, schema validation, error handling. Then smoke test it with a real request and show me the curl command. Tick items in TODO.md.
```

**Bug fix (pehle free tools, aakhir me prompt)**
```
Error: [PASTE FULL TRACEBACK]. File: [path]. Expected: [x]. Fix root cause only. Don't change unrelated code. Re-run to verify.
```

**Polish**
```
Add GET/POST /api/v1/demo/seed that loads realistic sample data for this problem, so the demo works in 10 seconds. Add reasoning/telemetry fields to responses (model, latency_ms, confidence, citations) and tags + summaries + example payloads for every route in /docs.
```

**Pitch (ye claude.ai/Gemini free chat me karo, prompt waste mat karo)**
```
Here's my project: [summary]. Write a 3-minute pitch: problem -> demo flow -> tech differentiators -> impact. Plus 5 tough judge questions with answers.
```

---

## E. Free Platforms Jo Tumhare Prompts Bachate Hain

| Kaam | Kaha karo |
|---|---|
| Error debug, SQL, regex, ideas | claude.ai / Gemini (AI Studio) / ChatGPT free chat |
| UI design (screenshot ya prompt se HTML) | v0.dev / Lovable / Bolt free tier -> HTML copy karke frontend/ me daalo |
| LLM prompt testing | Groq Playground / AI Studio, system prompt wahan perfect karo, phir code me paste |
| API testing | Swagger `/docs` (Postman ki zaroorat nahi) |
| Public demo link | Render / Railway free tier, ya `cloudflared tunnel` / ngrok |
| Pitch, slides, README | Free chat (prompts consume nahi) |

---

## F. 6-Ghante Timeline (4 Log)

| Time | Kaam |
|---|---|
| 0:00-0:20 | Problem padho, idea lock, roles baanto, Prompt 1 chalao |
| 0:20-2:30 | Core features (Prompts 2-6). Backend + frontend parallel |
| 2:30-3:30 | Integration, bugs. Pehla end-to-end demo chalna chahiye |
| 3:30-4:30 | Wow feature + demo seed + telemetry. **4:30 par feature freeze** |
| 4:30-5:15 | Bug fix, error states, deploy, backup demo video record karo |
| 5:15-6:00 | Pitch rehearsal x3. Nayi cheez add mat karo |

---

## G. Judges Ko Impress Karne Ke Rules

1. **Demo > code.** Ek smooth 3-minute flow, 10 half-working features se behtar hai.
2. **Telemetry badge**: model, latency, sources dikhao. Ye "AI engineering" jaisa lagta hai.
3. **Fallback**: demo me ek baar Groq key hata ke dikhao ki app phir bhi chalta hai (agar time ho).
4. **Seed endpoint**: demo hamesha 10 second me ready.
5. **Pitch me problem + impact pehle, tech baad me.**
6. **Offline backup**: demo video record rakho, Wi-Fi fail hone par bachayega.
