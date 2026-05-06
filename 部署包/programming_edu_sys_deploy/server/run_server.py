"""Local runner for the backend server."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    workers = max(1, int(os.getenv("SERVER_WORKERS", "1")))

    uvicorn.run(
        "server.app:app" if workers > 1 else __import__("server.app", fromlist=["app"]).app,
        host=os.getenv("SERVER_HOST", "127.0.0.1"),
        port=int(os.getenv("SERVER_PORT", "8000")),
        reload=os.getenv("SERVER_RELOAD", "false").lower() == "true",
        workers=workers,
    )


if __name__ == "__main__":
    main()
