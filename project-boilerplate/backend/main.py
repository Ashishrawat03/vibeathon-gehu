"""FastAPI entrypoint: CORS, health, and feature routers."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.transform import router as transform_router
from app.core.config import get_settings
from app.db.sqlite import init_db

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Persona Transformer API — rewrite a draft for any audience.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(transform_router, prefix="/api/v1")


@app.on_event("startup")
def initialize_database() -> None:
    init_db()


@app.get("/")
def root():
    return {
        "ok": True,
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
        "transform_batch": "/api/v1/transform/batch",
        "auth": "/api/v1/auth",
    }


@app.get("/api/health")
@app.get("/health")
def health():
    gemini = (settings.gemini_api_key or "").strip()
    gemini_ok = bool(gemini) and "your_gemini" not in gemini
    return {
        "ok": True,
        "has_key": bool(settings.groq_keys or settings.gemini_api_key.strip()),
        "providers": {
            "groq": bool(settings.groq_keys),
            "gemini": gemini_ok,
        },
        "models": {
            "groq_default": settings.groq_default_model,
            "gemini_default": settings.gemini_default_model,
        },
    }
