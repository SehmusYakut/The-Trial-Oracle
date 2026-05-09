"""
Vercel serverless entrypoint.
Adds the repo root to sys.path so `from backend.*` imports resolve,
then re-exports the FastAPI app object for Vercel's ASGI runner.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.main import app  # noqa: F401  – Vercel picks up `app` from this module
