"""Compliance service — orchestrates evaluation runs."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.api.schemas.compliance import (
  ComplianceEvaluateRequest,
  ComplianceEvaluateResponse,
  ComplianceFindingResponse,
  ComplianceFindingsListResponse,
  ComplianceRunDetailResponse,
)
from app.core.constants import JobStatus
from app.core.exceptions import NotFoundError
from app.database.repositories.compliance_repo import ComplianceRepository
from app.models.compliance_run import ComplianceRun


class ComplianceService:
  def __init__(self, db: Session) -> None:
    self.db = db
    self.repo = ComplianceRepository(db)

  async def start_evaluation(self, request: ComplianceEvaluateRequest) -> ComplianceEvaluateResponse:
    """Create compliance run and dispatch Celery evaluation task."""
    run = ComplianceRun(
      org_id=request.org_id,
      document_id=request.document_id,
      status=JobStatus.PENDING.value,
    )
    self.repo.add(run)
    self.repo.session.commit()

    # TODO: dispatch evaluate_compliance_task.delay(run.id, ...)
    return ComplianceEvaluateResponse(
      run_id=run.id,
      status=JobStatus.PENDING.value,
      message="Compliance evaluation queued",
    )

  def get_run(self, run_id: UUID) -> ComplianceRunDetailResponse:
    run = self.repo.get_by_id(run_id)
    if not run:
      raise NotFoundError("ComplianceRun", str(run_id))
    findings = self.repo.get_findings(run_id)
    return ComplianceRunDetailResponse(
      id=run.id,
      org_id=run.org_id,
      document_id=run.document_id,
      status=run.status,
      risk_score=run.risk_score,
      compliance_pct=run.compliance_pct,
      created_at=run.created_at,
      findings_count=len(findings),
    )

  def get_findings(self, run_id: UUID) -> ComplianceFindingsListResponse:
    if not self.repo.get_by_id(run_id):
      raise NotFoundError("ComplianceRun", str(run_id))
    findings = self.repo.get_findings(run_id)
    return ComplianceFindingsListResponse(
      items=[ComplianceFindingResponse.model_validate(f) for f in findings],
      total=len(findings),
    )
