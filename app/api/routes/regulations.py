"""Regulation management and ingestion endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.dependencies.pagination import get_pagination
from app.api.dependencies.services import get_regulation_service
from app.api.schemas.common import PaginationParams
from app.api.schemas.regulation import (
  RegulationListResponse,
  RegulationResponse,
  RegulationUploadResponse,
  RetryIngestionRequest,
  RetryIngestionResponse,
  VersionStatusResponse,
)
from app.core.constants import DocumentType, RegulatorCode
from app.services.regulation_service import RegulationService

router = APIRouter()


@router.post(
  "/admin/retry-ingestion",
  response_model=RetryIngestionResponse,
  summary="Re-enqueue pending or failed regulation ingestion tasks",
)
async def retry_ingestion(
  service: Annotated[RegulationService, Depends(get_regulation_service)],
  body: RetryIngestionRequest | None = None,
) -> RetryIngestionResponse:
  """Retry ingestion for selected versions or all pending/failed versions."""
  version_ids = body.version_ids if body else None
  res = service.retry_ingestion(version_ids=version_ids)
  return RetryIngestionResponse(**res)


@router.post(
  "/upload",
  response_model=RegulationUploadResponse,
  status_code=status.HTTP_202_ACCEPTED,
  summary="Upload regulatory PDF",
  description="Upload a regulatory document for parsing, clause extraction, embedding, and vector indexing.",
)
async def upload_regulation(
  service: Annotated[RegulationService, Depends(get_regulation_service)],
  file: UploadFile = File(..., description="Regulatory PDF file"),
  regulator_code: RegulatorCode = Form(..., description="Regulator code (RBI, SEBI, etc.)"),
  title: str = Form(..., description="Regulation title"),
  document_type: DocumentType = Form(..., description="Document type"),
  version: str = Form(..., description="Version identifier"),
) -> RegulationUploadResponse:
  """Trigger async regulatory document ingestion pipeline."""
  return await service.upload_and_ingest(
    file=file,
    regulator_code=regulator_code,
    title=title,
    document_type=document_type,
    version=version,
  )


@router.get(
  "",
  response_model=RegulationListResponse,
  summary="List regulations",
)
async def list_regulations(
  service: Annotated[RegulationService, Depends(get_regulation_service)],
  pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> RegulationListResponse:
  """List all ingested regulations with pagination."""
  return service.list_regulations(skip=pagination.skip, limit=pagination.limit)


@router.get(
  "/versions/{version_id}/status",
  response_model=VersionStatusResponse,
  summary="Get ingestion status for a specific version",
)
async def get_version_status(
  version_id: UUID,
  service: Annotated[RegulationService, Depends(get_regulation_service)],
) -> VersionStatusResponse:
  """Return ingestion status, error message, and clause count for a specific regulation version."""
  res = service.get_version_status(version_id)
  return VersionStatusResponse(**res)


@router.get(
  "/{regulation_id}",
  response_model=RegulationResponse,
  summary="Get regulation detail",
)
async def get_regulation(
  regulation_id: UUID,
  service: Annotated[RegulationService, Depends(get_regulation_service)],
) -> RegulationResponse:
  """Get regulation metadata and current version."""
  return service.get_regulation(regulation_id)


@router.get(
  "/{regulation_id}/status",
  summary="Poll ingestion status for a regulation",
)
async def get_regulation_status(
  regulation_id: UUID,
  service: Annotated[RegulationService, Depends(get_regulation_service)],
) -> dict:
  """Return the current ingestion status and clause count for the active version."""
  return service.get_regulation_status(regulation_id)

