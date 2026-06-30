"""Report API schemas."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReportFormat(StrEnum):
  JSON = "json"
  PDF = "pdf"


class ReportGenerateRequest(BaseModel):
  run_id: UUID
  format: ReportFormat = ReportFormat.JSON


class ReportResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  run_id: UUID
  format: str
  storage_path: str
  created_at: datetime


class ReportGenerateResponse(BaseModel):
  report_id: UUID
  status: str
  message: str
