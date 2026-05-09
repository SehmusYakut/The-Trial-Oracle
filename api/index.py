"""
Vercel serverless entrypoint.
Adds the repo root to sys.path so `from backend.*` imports resolve,
then re-exports the FastAPI app object for Vercel's ASGI runner.
"""
import sys
import os
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.main import app  # noqa: F401  – Vercel picks up `app` from this module
