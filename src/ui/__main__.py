"""Run the local UI:  python -m src.ui  →  http://localhost:8080 (DEMO_MODE on unless overridden)."""
import os

os.environ.setdefault("DEMO_MODE", "true")

import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run("src.ui.app:app", host=os.getenv("UI_HOST", "127.0.0.1"), port=int(os.getenv("UI_PORT", "8080")))
