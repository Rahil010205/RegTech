"""Compliance evaluation Celery task."""

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.evaluate_compliance.evaluate_compliance_task", bind=True)
def evaluate_compliance_task(
    self,
    run_id: str,
    regulator_codes: list[str],
    request_id: str | None = None,
) -> dict:
    """Run compliance evaluation for a document against selected regulators."""
    # TODO: implement pipeline
    return {"run_id": run_id, "status": "pending"}
