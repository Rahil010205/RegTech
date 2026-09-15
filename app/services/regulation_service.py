"""Regulation service — orchestrates regulatory document ingestion."""

from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.api.schemas.regulation import (
  RegulationListResponse,
  RegulationResponse,
  RegulationUploadResponse,
  RegulationVersionResponse,
)
from app.core.constants import DocumentType, JobStatus, RegulatorCode
from app.core.exceptions import NotFoundError
from app.database.repositories.regulation_repo import RegulationRepository
from app.models.compliance_run import IngestionJob
from app.models.regulation import Regulation, RegulationVersion


class RegulationService:
  def __init__(self, db: Session) -> None:
    self.db = db
    self.repo = RegulationRepository(db)

  async def upload_and_ingest(
    self,
    file: UploadFile,
    regulator_code: RegulatorCode,
    title: str,
    document_type: DocumentType,
    version: str,
  ) -> RegulationUploadResponse:
    """Save file, create DB records, handle duplicate hashes, and dispatch Celery task.

    The method now:
    1. Reads the uploaded file bytes once.
    2. Computes a SHA‑256 hash of the exact bytes.
    3. Checks for an existing ``RegulationVersion`` with the same ``content_hash``.
       If found, raises ``ConflictError`` which the global exception handler maps to 409.
    4. Persists ``Regulation`` and ``RegulationVersion`` (with the hash) and flushes to
       obtain their IDs.
    5. Creates an ``IngestionJob`` referencing the ``RegulationVersion``.
    6. Commits the transaction.
    7. Saves the raw PDF to ``settings.raw_data_dir`` and, if the Celery task exists,
       dispatches ``ingest_regulation_task`` *after* the commit.
    """
    import hashlib
    from pathlib import Path
    from app.core.exceptions import ConflictError
    from app.core.config import get_settings
    from app.workers.tasks.ingest_regulation import ingest_regulation_task

    # 1. Read file bytes once
    raw_bytes = await file.read()
    # 2. Compute SHA‑256 hash
    content_hash = hashlib.sha256(raw_bytes).hexdigest()

    # 3. Check for duplicate content hash
    existing_version = (
        self.repo.session.query(RegulationVersion)
        .filter_by(content_hash=content_hash)
        .first()
    )
    if existing_version:
        raise ConflictError("This regulation file has already been uploaded.")

    # 4. Create Regulation and RegulationVersion records
    regulation = Regulation(
        regulator_code=regulator_code.value,
        title=title,
        document_type=document_type.value,
    )
    self.repo.add(regulation)

    reg_version = RegulationVersion(
        regulation_id=regulation.id,
        version=version,
        content_hash=content_hash,
        status=JobStatus.PENDING.value,
        is_current=True,
    )
    self.repo.session.add(reg_version)

    # Flush to generate IDs for both objects before creating the job
    self.repo.session.flush()

    # 5. Create IngestionJob linked to the version
    job = IngestionJob(
        entity_type="regulation_version",
        entity_id=reg_version.id,
        status=JobStatus.PENDING.value,
    )
    self.repo.session.add(job)

    settings = get_settings()
    raw_dir = settings.raw_data_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    file_path = raw_dir / f"{reg_version.id}.pdf"
    file_path.write_bytes(raw_bytes)

    reg_version.storage_path = str(file_path)

    # 6. Commit the transaction
    self.repo.session.commit()

    # 7. Dispatch Celery task (if defined)
    try:
        ingest_regulation_task.delay(str(reg_version.id), str(file_path))
    except Exception:
        pass

    return RegulationUploadResponse(
        regulation_id=regulation.id,
        version_id=reg_version.id,
        job_id=job.id,
        status=JobStatus.PENDING.value,
        message="Regulatory document ingestion queued",
    )



  def list_regulations(self, skip: int = 0, limit: int = 50) -> RegulationListResponse:
    items = self.repo.list_all(skip=skip, limit=limit)
    return RegulationListResponse(
      items=[self._to_response(r) for r in items],
      total=len(items),
      skip=skip,
      limit=limit,
    )

  def get_regulation(self, regulation_id: UUID) -> RegulationResponse:
    regulation = self.repo.get_by_id(regulation_id)
    if not regulation:
      raise NotFoundError("Regulation", str(regulation_id))
    return self._to_response(regulation)

  def _to_response(self, regulation: Regulation) -> RegulationResponse:
    from sqlalchemy import func, select
    from app.models.clause import Clause

    current = self.repo.get_current_version(regulation.id)
    clause_count = 0
    version_response = None
    if current:
      clause_count = self.db.scalar(
        select(func.count()).select_from(Clause).where(Clause.version_id == current.id)
      ) or 0
      version_response = RegulationVersionResponse(
        id=current.id,
        version=current.version,
        effective_date=current.effective_date,
        is_current=current.is_current,
        status=current.status,
        clause_count=clause_count,
        error_message=getattr(current, "error_message", None),
        created_at=current.created_at,
      )

    return RegulationResponse(
      id=regulation.id,
      regulator_code=regulation.regulator_code,
      title=regulation.title,
      document_type=regulation.document_type,
      created_at=regulation.created_at,
      current_version=version_response,
      clause_count=clause_count,
    )

  def get_regulation_status(self, regulation_id: UUID) -> dict:
    """Return the ingestion status and clause count for the current version."""
    from sqlalchemy import func, select
    from app.models.clause import Clause

    regulation = self.repo.get_by_id(regulation_id)
    if not regulation:
      raise NotFoundError("Regulation", str(regulation_id))

    current = self.repo.get_current_version(regulation.id)
    if not current:
      return {"status": "pending", "clause_count": 0, "version_id": None}

    clause_count: int = self.db.scalar(
      select(func.count()).select_from(Clause).where(Clause.version_id == current.id)
    ) or 0

    return {
      "regulation_id": str(regulation_id),
      "version_id": str(current.id),
      "status": current.status,
      "clause_count": clause_count,
    }

  def get_version_status(self, version_id: UUID) -> dict:
    """Return the ingestion status, error message, and clause count for a specific version."""
    from sqlalchemy import func, select
    from app.models.clause import Clause

    version = self.db.get(RegulationVersion, version_id)
    if not version:
      raise NotFoundError("RegulationVersion", str(version_id))

    clause_count: int = self.db.scalar(
      select(func.count()).select_from(Clause).where(Clause.version_id == version.id)
    ) or 0

    return {
      "version_id": str(version.id),
      "regulation_id": str(version.regulation_id),
      "status": version.status,
      "clause_count": clause_count,
      "error_message": getattr(version, "error_message", None),
    }

  def retry_ingestion(self, version_ids: list[UUID] | None = None) -> dict:
    """
    Re-enqueue pending or failed regulation version ingestion tasks.

    If version_ids is provided, retries those specific versions.
    Otherwise, retries all versions with status 'pending' or 'failed'.
    """
    from pathlib import Path
    from sqlalchemy import select
    from app.core.config import get_settings
    from app.workers.tasks.ingest_regulation import ingest_regulation_task

    query = select(RegulationVersion)
    if version_ids:
      query = query.where(RegulationVersion.id.in_(version_ids))
    else:
      query = query.where(RegulationVersion.status.in_([JobStatus.PENDING.value, JobStatus.FAILED.value]))

    versions = list(self.db.scalars(query).all())
    requeued: list[str] = []
    skipped: list[str] = []

    settings = get_settings()

    for ver in versions:
      # Locate the PDF file path
      file_path = None
      if ver.storage_path and Path(ver.storage_path).exists():
        file_path = Path(ver.storage_path)
      else:
        candidate = settings.raw_data_dir / f"{ver.id}.pdf"
        if candidate.exists():
          file_path = candidate

      if not file_path:
        skipped.append(f"{ver.id} (PDF file not found on disk)")
        continue

      # Reset version status
      ver.status = JobStatus.PENDING.value
      ver.error_message = None
      if not ver.storage_path:
        ver.storage_path = str(file_path)

      # Locate or create job
      job = self.db.scalar(
        select(IngestionJob)
        .where(IngestionJob.entity_id == ver.id)
        .order_by(IngestionJob.created_at.desc())
      )
      if job:
        job.status = JobStatus.PENDING.value
        job.error_message = None
        if hasattr(job, "retry_count"):
          job.retry_count = (job.retry_count or 0) + 1
      else:
        job = IngestionJob(
          entity_type="regulation_version",
          entity_id=ver.id,
          status=JobStatus.PENDING.value,
        )
        self.db.add(job)

      self.db.commit()

      try:
        ingest_regulation_task.delay(str(ver.id), str(file_path))
        requeued.append(str(ver.id))
      except Exception as e:
        skipped.append(f"{ver.id} (Failed to dispatch task: {e})")

    return {
      "requeued": requeued,
      "skipped": skipped,
      "message": f"Requeued {len(requeued)} ingestion task(s), skipped {len(skipped)}.",
    }


