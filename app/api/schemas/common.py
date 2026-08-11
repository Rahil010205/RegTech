"""Shared API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
  error_code: str
  message: str
  details: dict[str, Any] = Field(default_factory=dict)
  request_id: str | None = None


class PaginationParams(BaseModel):
  skip: int = Field(0, ge=0)
  limit: int = Field(50, ge=1, le=100)


class PaginatedResponse(BaseModel):
  total: int
  skip: int
  limit: int


class MessageResponse(BaseModel):
  message: str


class ServiceStatus(BaseModel):
  connected: bool
  error: str | None = None


class HealthResponse(BaseModel):
  """Response shape for GET /health."""
  status: str  # "ok" | "degraded"
  db: ServiceStatus
  qdrant: ServiceStatus


class TimestampSchema(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  created_at: datetime
  updated_at: datetime | None = None


class IDResponse(BaseModel):
  id: UUID
