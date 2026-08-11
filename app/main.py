"""Entry-point alias so the server can be launched as:

    uvicorn app.main:app --reload

The actual application factory lives in the project-root ``main.py``; this
module simply imports and re-exports the ``app`` instance so both launch
styles work:

    uvicorn main:app --reload          # from project root
    uvicorn app.main:app --reload      # per Phase-0 spec
"""

from main import app  # noqa: F401  (re-export)

__all__ = ["app"]
