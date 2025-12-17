"""
Vercel Flask entrypoint.

Vercel's Python runtime looks for an `app` object in common entrypoints
like `api/index.py`. We re-export the Flask app instance created in `run.py`.
"""

from run import app  # noqa: F401

