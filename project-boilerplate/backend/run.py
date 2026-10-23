"""
run.py - Entrypoint Script to Run `main.py` FastAPI Server
----------------------------------------------------------
Run command (using uv):
    uv run python run.py
Or after activating `.venv`:
    python run.py
"""

import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()


def start_server():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("RELOAD", "true").lower() in ("true", "1", "yes")
    log_level = "debug" if os.getenv("DEBUG", "true").lower() == "true" else "info"

    print("=" * 65)
    print(f"🔥 Launching FastAPI Server via run.py")
    print(f"🌐 Local URL   : http://localhost:{port}")
    print(f"📚 Swagger Docs: http://localhost:{port}/docs")
    print(f"❤️  Health Check: http://localhost:{port}/api/health")
    print(f"♻️  Auto-Reload : {reload_enabled}")
    print("=" * 65)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload_enabled,
        log_level=log_level,
    )


if __name__ == "__main__":
    start_server()
