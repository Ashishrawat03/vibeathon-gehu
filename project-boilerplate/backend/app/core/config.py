"""
config.py - Central settings (reads backend/.env)
Usage: from app.core.config import get_settings; s = get_settings()
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env.test", extra="ignore")

    app_name: str = "Hackathon-AI-Backend"

    # Groq: single key OR comma-separated keys (GROQ_API_KEYS="k1,k2,k3")
    groq_api_key: str = ""
    groq_api_keys: str = ""
    groq_default_model: str = "llama-3.3-70b-versatile"
    groq_fast_model: str = "llama-3.1-8b-instant"
    groq_reasoning_model: str = "openai/gpt-oss-120b"
    groq_whisper_model: str = "whisper-large-v3-turbo"

    gemini_api_key: str = ""
    gemini_default_model: str = "gemini-2.5-flash"
    gemini_pro_model: str = "gemini-2.5-pro"

    hf_token: str = ""
    hf_embedding_model: str = "BAAI/bge-small-en-v1.5"
    hf_embedding_dim: int = 384

    jwt_secret: str = "local-development-only-change-this-secret"

    @property
    def groq_keys(self) -> list[str]:
        """All usable Groq keys (deduped, placeholders ignored)."""
        raw = f"{self.groq_api_keys},{self.groq_api_key}".split(",")
        keys: list[str] = []
        for k in (x.strip().strip('"') for x in raw):
            if k and "your_groq" not in k and k not in keys:
                keys.append(k)
        return keys


@lru_cache
def get_settings() -> Settings:
    return Settings()
