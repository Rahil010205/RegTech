"""Celery application configuration."""

from celery import Celery

from app.core.config import get_settings
from app.core.constants import (
    QUEUE_COMPLIANCE,
    QUEUE_EMBEDDING,
    QUEUE_INGESTION,
    QUEUE_REPORTS,
)

settings = get_settings()

celery_app = Celery(
    "regtech",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks.ingest_regulation",
        "app.workers.tasks.ingest_document",
        "app.workers.tasks.embed_clauses",
        "app.workers.tasks.evaluate_compliance",
        "app.workers.tasks.generate_report",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.ingest_*": {"queue": QUEUE_INGESTION},
        "app.workers.tasks.embed_*": {"queue": QUEUE_EMBEDDING},
        "app.workers.tasks.evaluate_*": {"queue": QUEUE_COMPLIANCE},
        "app.workers.tasks.generate_*": {"queue": QUEUE_REPORTS},
    },
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
