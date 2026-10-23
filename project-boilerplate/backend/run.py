"""
run.py - Entrypoint Script to Run `main.py` FastAPI Server
----------------------------------------------------------
Run command (using uv):
    uv run python run.py
Or after activating `.venv`:
    python run.py
"""

import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env.test")


def start_server():
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("RELOAD", "true").lower() in ("true", "1", "yes")
    log_level = "debug" if os.getenv("DEBUG", "true").lower() == "true" else "info"

    print("=" * 65)
    print("Launching FastAPI Server via run.py")
    print(f"Local URL   : http://127.0.0.1:{port}")
    print(f"Swagger Docs: http://127.0.0.1:{port}/docs")
    print(f"Health Check: http://127.0.0.1:{port}/api/health")
    print(f"Auto-Reload : {reload_enabled}")
    print("=" * 65)

    uvicorn.run(
        "main:app",
        app_dir=str(BACKEND_DIR),
        host=host,
        port=port,
        reload=reload_enabled,
        log_level=log_level,
    )


if __name__ == "__main__":
    start_server()
