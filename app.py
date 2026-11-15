"""
Omni-Indic Translation Suite — Hugging Face Spaces / Cloud Entrypoint
======================================================================
Imports and exposes the FastAPI application instance for direct deployment
on Hugging Face Spaces, Render, Railway, or any ASGI runner.
"""

import os
import sys
from pathlib import Path

# Add project root and api directories to Python search path
PROJECT_ROOT = Path(__file__).resolve().parent
API_DIR = PROJECT_ROOT / "api"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

# Ensure production mode by default on cloud deployments
if "DEMO_MODE" not in os.environ:
    os.environ["DEMO_MODE"] = "false"

from api.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
