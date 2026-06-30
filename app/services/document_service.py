"""Document service — orchestrates organization document ingestion."""

from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.api.schemas.document import (
  DocumentDetailResponse,
  DocumentListResponse,
  DocumentResponse,
  DocumentUploadResponse,
)
from app.core.constants import DocumentType, JobStatus
from app.core.exceptions import NotFoundError
from app.database.repositories.document_repo import DocumentRepository
from app.models.compliance_run import IngestionJob
from app.models.document import Document


class DocumentService:
  def __init__(self, db: Session) -> None:
    self.db = db
    self.repo = DocumentRepository(db)

  async def upload_and_ingest(
    self,
    file: UploadFile,
    org_id: UUID,
    doc_type: DocumentType,
  ) -> DocumentUploadResponse:
    """Save file, create DB records, dispatch Celery ingestion task."""
    document = Document(
      org_id=org_id,
      filename=file.filename or "unknown.pdf",
      doc_type=doc_type.value,
      content_hash="",  # TODO: compute hash after save
      status=JobStatus.PENDING.value,
    )
    self.repo.add(document)

    job = IngestionJob(
      entity_type="document",
      entity_id=document.id,
      status=JobStatus.PENDING.value,
    )
    self.repo.session.add(job)
    self.repo.session.commit()

    # TODO: save file, dispatch ingest_document_task.delay(...)
    return DocumentUploadResponse(
      document_id=document.id,
      job_id=job.id,
      status=JobStatus.PENDING.value,
      message="Document ingestion queued",
    )

  def list_documents(self, org_id: UUID, skip: int = 0, limit: int = 50) -> DocumentListResponse:
    items = self.repo.list_by_org(org_id, skip=skip, limit=limit)
    return DocumentListResponse(
      items=[DocumentResponse.model_validate(d) for d in items],
      total=len(items),
      skip=skip,
      limit=limit,
    )

  def get_document(self, document_id: UUID) -> DocumentDetailResponse:
    document = self.repo.get_by_id(document_id)
    if not document:
      raise NotFoundError("Document", str(document_id))
    return DocumentDetailResponse.model_validate(document)
