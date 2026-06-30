"""Report generation Celery task."""

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.generate_report.generate_report_task", bind=True)
def generate_report_task(self, report_id: str, request_id: str | None = None) -> dict:
    """Generate compliance report (JSON or PDF)."""
    # TODO: implement pipeline
    return {"report_id": report_id, "status": "pending"}
