"""
main.py - Core FastAPI Application Setup
----------------------------------------
Ye file sirf FastAPI app initialize karti hai, CORS configure karti hai,
aur basic health/status routes deti hai.
Jab AI agent (Claude/Cursor) project build karega, wo `app/api/routes/` ke routers
yahan `app.include_router(...)` ke through connect karega.
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.core.config import get_settings

# Load environment variables from .env file
load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Hackathon-AI-Backend")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
APP_ENV = os.getenv("APP_ENV", "development")

# Parse CORS origins from .env
raw_origins = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle hook.
    AI Agent can initialize DB pools, AI clients (Groq/Gemini/HF), or caches here.
    """
    print(f"\n🚀 Starting {APP_NAME} (v{APP_VERSION}) in [{APP_ENV}] mode...")
    yield
    print(f"\n🛑 Shutting down {APP_NAME} cleanly...")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Hackathon AI Backend Boilerplate (FastAPI + uv + Groq + Gemini + HuggingFace + Supabase)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware (Frontend connection ke liye)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if "*" not in CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint to verify server is live."""
    return {
        "status": "online",
        "service": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "docs": "/docs",
        "message": "FastAPI Backend is running! Visit /docs for Swagger UI.",
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint for frontend & deployment monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ai_stack_configured": {
            "groq_key_set": bool(get_settings().groq_keys),
            "gemini_key_set": bool(os.getenv("GEMINI_API_KEY")),
            "hf_token_set": bool(os.getenv("HF_TOKEN")),
            "supabase_configured": bool(os.getenv("SUPABASE_URL")),
        },
    }


# ==============================================================================
# TODO FOR AI AGENT: Register Modular API Routers Below
# ==============================================================================
# Example:
# from app.api.routes import auth, chat, rag
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
# app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chat"])
# app.include_router(rag.router, prefix="/api/v1/rag", tags=["RAG & Embeddings"])
