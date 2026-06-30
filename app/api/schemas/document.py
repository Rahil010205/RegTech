"""Document API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import DocumentType


class DocumentUpload(BaseModel):
  org_id: UUID
  doc_type: DocumentType


class DocumentSectionResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  section_number: str
  text: str


class DocumentResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  org_id: UUID
  filename: str
  doc_type: str
  status: str
  content_hash: str
  created_at: datetime


class DocumentDetailResponse(DocumentResponse):
  sections: list[DocumentSectionResponse] = []


class DocumentListResponse(BaseModel):
  items: list[DocumentResponse]
  total: int
  skip: int
  limit: int


class DocumentUploadResponse(BaseModel):
  document_id: UUID
  job_id: UUID
  status: str
  message: str
