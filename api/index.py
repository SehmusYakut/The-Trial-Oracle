"""
Vercel serverless entrypoint.
Adds the repo root to sys.path so `from backend.*` imports resolve,
then re-exports the FastAPI app object for Vercel's ASGI runner.
"""
import sys
import os
from pathlib import Path

root_path = str(Path(__file__).resolve().parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from backend.main import app  # noqa: F401  – Vercel picks up `app` from this module
