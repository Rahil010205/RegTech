"""Regulation API schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import DocumentType, RegulatorCode


class RegulationCreate(BaseModel):
  regulator_code: RegulatorCode
  title: str = Field(..., min_length=1, max_length=500)
  document_type: DocumentType
  version: str = Field(..., min_length=1, max_length=50)
  effective_date: date | None = None


class RegulationVersionResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  version: str
  effective_date: date | None
  is_current: bool
  status: str
  clause_count: int = 0
  error_message: str | None = None
  created_at: datetime


class RegulationResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  regulator_code: str
  title: str
  document_type: str
  created_at: datetime
  current_version: RegulationVersionResponse | None = None
  clause_count: int = 0


class RegulationListResponse(BaseModel):
  items: list[RegulationResponse]
  total: int
  skip: int
  limit: int


class RegulationUploadResponse(BaseModel):
  regulation_id: UUID
  version_id: UUID
  job_id: UUID
  status: str
  message: str


class VersionStatusResponse(BaseModel):
  """Detailed status for a specific regulation version."""
  version_id: UUID
  regulation_id: UUID
  status: str
  clause_count: int = 0
  error_message: str | None = None


class RetryIngestionRequest(BaseModel):
  """Request body for the admin retry endpoint."""
  version_ids: list[UUID] | None = None


class RetryIngestionResponse(BaseModel):
  requeued: list[str]
  skipped: list[str]
  message: str
