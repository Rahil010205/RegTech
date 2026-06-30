"""Regulatory document ingestion Celery task."""

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.ingest_regulation.ingest_regulation_task", bind=True)
def ingest_regulation_task(self, version_id: str, file_path: str, request_id: str | None = None) -> dict:
    """
    Full regulatory ingestion pipeline:
    PDF → clauses → PostgreSQL → embeddings → Qdrant
    """
    # TODO: implement pipeline
    return {"version_id": version_id, "status": "pending"}
