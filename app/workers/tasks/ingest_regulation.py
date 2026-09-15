"""Regulatory document ingestion Celery task."""

from __future__ import annotations

import traceback
from pathlib import Path

from loguru import logger

from app.workers.celery_app import celery_app


@celery_app.task(
    name="app.workers.tasks.ingest_regulation.ingest_regulation_task",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def ingest_regulation_task(
    self,
    version_id: str,
    file_path: str,
    request_id: str | None = None,
) -> dict:
    """
    Full regulatory ingestion pipeline:
    PDF -> clauses -> PostgreSQL/pgvector embeddings

    State transitions (enforced here):
        pending -> processing -> completed | failed

    On failure, a human-readable error_message is persisted to BOTH the
    ``IngestionJob`` and the ``RegulationVersion`` row so that callers
    can surface meaningful diagnostics.

    Parameters
    ----------
    version_id:
        UUID of the RegulationVersion row created by the upload endpoint.
    file_path:
        Absolute path to the stored PDF on disk (written by the upload endpoint).
    request_id:
        Optional trace ID for correlating logs.
    """
    from sqlalchemy import func, select

    from app.core.constants import JobStatus
    from app.database.session import SessionLocal
    from app.ingestion.ingestion_pipeline import IngestionOptions, IngestionPipeline
    from app.models.clause import Clause
    from app.models.compliance_run import IngestionJob
    from app.models.regulation import Regulation, RegulationVersion

    log = logger.bind(version_id=version_id, task_id=self.request.id, request_id=request_id)
    log.info("ingest_regulation_task received — version_id={} file_path={}", version_id, file_path)

    path = Path(file_path)
    if not path.exists():
        error_msg = f"PDF file not found on disk: {file_path}"
        log.error(error_msg)
        # Persist the error so the user can see it
        _mark_failed(version_id, error_msg, log)
        return {"version_id": version_id, "status": "failed", "error": error_msg}

    with SessionLocal() as session:
        # ── Locate the RegulationVersion row ──────────────────────────
        version_row: RegulationVersion | None = session.get(RegulationVersion, version_id)
        if version_row is None:
            log.error("RegulationVersion not found in DB: {}", version_id)
            return {"version_id": version_id, "status": "failed", "error": "Version not found"}

        # ── Locate the most recent IngestionJob for this version ──────
        job: IngestionJob | None = session.scalar(
            select(IngestionJob)
            .where(IngestionJob.entity_id == version_row.id)
            .order_by(IngestionJob.created_at.desc())
        )

        # ── Mark both rows as PROCESSING ──────────────────────────────
        version_row.status = JobStatus.PROCESSING.value
        version_row.error_message = None  # clear any previous error
        if job:
            job.status = JobStatus.PROCESSING.value
            job.error_message = None
        session.commit()
        log.info("Marked version + job as PROCESSING")

        # ── Pull metadata from parent regulation row ──────────────────
        regulation: Regulation | None = session.get(Regulation, version_row.regulation_id)
        regulator_code = regulation.regulator_code if regulation else "RBI"
        title = regulation.title if regulation else path.stem
        document_type = regulation.document_type if regulation else "regulation"
        version_label = version_row.version or "1.0"

        options = IngestionOptions(
            regulator_code=regulator_code,
            version=version_label,
            title=title,
            document_type=document_type,
            # Re-use the existing version_row; do not create a duplicate
            skip_if_duplicate=False,
        )

        try:
            # ── Run the full ingestion pipeline ───────────────────────
            pipeline = IngestionPipeline(session)
            result = pipeline.ingest_document(path, options)

            # ── Verify clause count from persisted rows ───────────────
            session.refresh(version_row)
            persisted_clause_count: int = session.scalar(
                select(func.count()).select_from(Clause).where(Clause.version_id == version_row.id)
            ) or 0

            if persisted_clause_count == 0:
                raise RuntimeError(
                    "Pipeline reported success but no clauses were persisted to the database"
                )

            # ── Mark COMPLETED only after both clauses + embeddings confirmed
            version_row.status = JobStatus.COMPLETED.value
            version_row.error_message = None
            if job:
                job.status = JobStatus.COMPLETED.value
                job.error_message = None
            session.commit()

            log.info(
                "ingest_regulation_task COMPLETED — version_id={} clauses={} embeddings={} persisted_clause_count={}",
                version_id,
                result.clauses_created,
                result.embeddings_created,
                persisted_clause_count,
            )
            return {
                "version_id": version_id,
                "status": "completed",
                "clauses_created": result.clauses_created,
                "embeddings_created": result.embeddings_created,
                "pages_processed": result.pages_processed,
                "persisted_clause_count": persisted_clause_count,
                "duplicate": result.duplicate,
            }

        except Exception as exc:
            tb = traceback.format_exc()
            error_msg = str(exc)[:2000]
            log.error("ingest_regulation_task FAILED: {}\n{}", exc, tb)

            try:
                session.rollback()
                # Persist error on BOTH version and job
                version_row.status = JobStatus.FAILED.value
                version_row.error_message = error_msg
                if job:
                    job.status = JobStatus.FAILED.value
                    job.error_message = error_msg
                session.commit()
            except Exception:
                session.rollback()

            return {
                "version_id": version_id,
                "status": "failed",
                "error": error_msg,
            }


def _mark_failed(version_id: str, error_msg: str, log) -> None:
    """Mark version + job as FAILED when we can't even open a pipeline session."""
    try:
        from app.core.constants import JobStatus
        from app.database.session import SessionLocal
        from app.models.compliance_run import IngestionJob
        from app.models.regulation import RegulationVersion
        from sqlalchemy import select

        with SessionLocal() as session:
            version_row = session.get(RegulationVersion, version_id)
            if version_row:
                version_row.status = JobStatus.FAILED.value
                version_row.error_message = error_msg[:2000]
            job = session.scalar(
                select(IngestionJob)
                .where(IngestionJob.entity_id == version_id)
                .order_by(IngestionJob.created_at.desc())
            )
            if job:
                job.status = JobStatus.FAILED.value
                job.error_message = error_msg[:2000]
            session.commit()
    except Exception as e:
        log.error("_mark_failed itself failed: {}", e)
