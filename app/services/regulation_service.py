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
    """Save file, create DB records, dispatch Celery ingestion task."""
    regulation = Regulation(
      regulator_code=regulator_code.value,
      title=title,
      document_type=document_type.value,
    )
    self.repo.add(regulation)

    reg_version = RegulationVersion(
      regulation_id=regulation.id,
      version=version,
      content_hash="",  # TODO: compute hash after save
      status=JobStatus.PENDING.value,
      is_current=True,
    )
    self.repo.session.add(reg_version)

    job = IngestionJob(
      entity_type="regulation_version",
      entity_id=reg_version.id,
      status=JobStatus.PENDING.value,
    )
    self.repo.session.add(job)
    self.repo.session.commit()

    # TODO: save file to data/raw/, dispatch ingest_regulation_task.delay(...)
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
    current = self.repo.get_current_version(regulation.id)
    return RegulationResponse(
      id=regulation.id,
      regulator_code=regulation.regulator_code,
      title=regulation.title,
      document_type=regulation.document_type,
      created_at=regulation.created_at,
      current_version=RegulationVersionResponse.model_validate(current) if current else None,
    )
