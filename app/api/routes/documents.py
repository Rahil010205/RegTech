"""Organization document endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.dependencies.pagination import get_pagination
from app.api.dependencies.services import get_document_service
from app.api.schemas.common import PaginationParams
from app.api.schemas.document import (
  DocumentDetailResponse,
  DocumentListResponse,
  DocumentUploadResponse,
)
from app.core.constants import DocumentType
from app.services.document_service import DocumentService

router = APIRouter()


@router.post(
  "/upload",
  response_model=DocumentUploadResponse,
  status_code=status.HTTP_202_ACCEPTED,
  summary="Upload organization document",
  description="Upload a policy/SOP document for parsing and compliance evaluation.",
)
async def upload_document(
  service: Annotated[DocumentService, Depends(get_document_service)],
  file: UploadFile = File(..., description="Organization PDF file"),
  org_id: UUID = Form(..., description="Organization ID"),
  doc_type: DocumentType = Form(..., description="Document type (policy, sop, etc.)"),
) -> DocumentUploadResponse:
  """Trigger async organization document ingestion."""
  return await service.upload_and_ingest(file=file, org_id=org_id, doc_type=doc_type)


@router.get(
  "",
  response_model=DocumentListResponse,
  summary="List organization documents",
)
async def list_documents(
  service: Annotated[DocumentService, Depends(get_document_service)],
  pagination: Annotated[PaginationParams, Depends(get_pagination)],
  org_id: UUID,
) -> DocumentListResponse:
  """List documents for an organization."""
  return service.list_documents(org_id=org_id, skip=pagination.skip, limit=pagination.limit)


@router.get(
  "/{document_id}",
  response_model=DocumentDetailResponse,
  summary="Get document detail",
)
async def get_document(
  document_id: UUID,
  service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentDetailResponse:
  """Get document metadata and parsed sections."""
  return service.get_document(document_id)
