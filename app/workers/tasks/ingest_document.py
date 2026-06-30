"""Organization document ingestion Celery task."""

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.ingest_document.ingest_document_task", bind=True)
def ingest_document_task(self, document_id: str, file_path: str, request_id: str | None = None) -> dict:
    """Parse org document into sections and persist to PostgreSQL."""
    # TODO: implement pipeline
    return {"document_id": document_id, "status": "pending"}
