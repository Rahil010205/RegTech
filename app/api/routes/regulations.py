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
)
from app.core.constants import DocumentType, RegulatorCode
from app.services.regulation_service import RegulationService

router = APIRouter()


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
