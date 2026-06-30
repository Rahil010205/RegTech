"""Compliance evaluation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies.services import get_compliance_service
from app.api.schemas.compliance import (
  ComplianceEvaluateRequest,
  ComplianceEvaluateResponse,
  ComplianceFindingsListResponse,
  ComplianceRunDetailResponse,
)
from app.services.compliance_service import ComplianceService

router = APIRouter()


@router.post(
  "/evaluate",
  response_model=ComplianceEvaluateResponse,
  status_code=status.HTTP_202_ACCEPTED,
  summary="Start compliance evaluation",
  description="Evaluate an organization document against selected regulatory frameworks.",
)
async def evaluate_compliance(
  request: ComplianceEvaluateRequest,
  service: Annotated[ComplianceService, Depends(get_compliance_service)],
) -> ComplianceEvaluateResponse:
  """Trigger async compliance evaluation job."""
  return await service.start_evaluation(request)


@router.get(
  "/runs/{run_id}",
  response_model=ComplianceRunDetailResponse,
  summary="Get compliance run status",
)
async def get_compliance_run(
  run_id: UUID,
  service: Annotated[ComplianceService, Depends(get_compliance_service)],
) -> ComplianceRunDetailResponse:
  """Get compliance evaluation run status and summary scores."""
  return service.get_run(run_id)


@router.get(
  "/runs/{run_id}/findings",
  response_model=ComplianceFindingsListResponse,
  summary="List compliance findings",
)
async def list_findings(
  run_id: UUID,
  service: Annotated[ComplianceService, Depends(get_compliance_service)],
) -> ComplianceFindingsListResponse:
  """List per-clause compliance findings for a run."""
  return service.get_findings(run_id)
