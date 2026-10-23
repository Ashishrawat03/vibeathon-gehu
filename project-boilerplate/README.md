# Persona Transformer

Persona Transformer is a Next.js frontend backed by a FastAPI service. The backend uses SQLite for user accounts and generated outputs; no external database or auth provider is required.

## Run locally

1. Configure the backend:

   ```powershell
   cd backend
   Copy-Item .env.example .env
   # Set GROQ_API_KEYS or GEMINI_API_KEY and replace JWT_SECRET.
   uv sync
   uv run python run.py
   ```

   FastAPI starts at `http://127.0.0.1:8000`. SQLite initializes automatically at `backend/app/data/app.db`.

2. In another terminal, configure and run the frontend:

   ```powershell
   cd frontend
   # Optional: set BACKEND_URL=http://127.0.0.1:8000 in .env.local
   npm install
   npm run dev
   ```

   Open `http://localhost:3000`. The frontend API routes proxy requests to the backend; use the `BACKEND_URL` environment variable if it is hosted elsewhere.

## Accounts and generated output

- Sign-up and login are handled by FastAPI at `/api/v1/auth/signup` and `/api/v1/auth/login`.
- Passwords are stored as salted PBKDF2 hashes. API access uses a signed bearer token.
- Users, chats, rewritten outputs, and output feedback are stored in SQLite.
- Configure a long random `JWT_SECRET` before deployment. The built-in default is for local development only.
- Set at least one supported LLM credential (`GROQ_API_KEYS` or `GEMINI_API_KEY`) to enable rewriting.

## API health

- Backend health: `http://127.0.0.1:8000/api/health`
- Interactive API docs: `http://127.0.0.1:8000/docs`
