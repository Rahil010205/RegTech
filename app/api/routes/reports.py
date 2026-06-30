"""Compliance report endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies.services import get_report_service
from app.api.schemas.report import ReportGenerateRequest, ReportGenerateResponse, ReportResponse
from app.services.report_service import ReportService

router = APIRouter()


@router.post(
  "/generate",
  response_model=ReportGenerateResponse,
  status_code=status.HTTP_202_ACCEPTED,
  summary="Generate compliance report",
)
async def generate_report(
  request: ReportGenerateRequest,
  service: Annotated[ReportService, Depends(get_report_service)],
) -> ReportGenerateResponse:
  """Trigger async report generation (JSON or PDF)."""
  return await service.generate(request)


@router.get(
  "/{report_id}",
  response_model=ReportResponse,
  summary="Get report metadata",
)
async def get_report(
  report_id: UUID,
  service: Annotated[ReportService, Depends(get_report_service)],
) -> ReportResponse:
  """Get report metadata and download path."""
  return service.get_report(report_id)
