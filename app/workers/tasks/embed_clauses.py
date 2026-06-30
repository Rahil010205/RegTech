"""Clause re-embedding Celery task."""

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.embed_clauses.embed_clauses_task", bind=True)
def embed_clauses_task(self, version_id: str, request_id: str | None = None) -> dict:
    """Re-embed clauses for a regulation version (model upgrade or re-index)."""
    # TODO: implement pipeline
    return {"version_id": version_id, "status": "pending"}
