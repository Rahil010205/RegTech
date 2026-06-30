"""Report service — orchestrates report generation."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.api.schemas.report import ReportGenerateRequest, ReportGenerateResponse, ReportResponse
from app.core.constants import JobStatus
from app.core.exceptions import NotFoundError
from app.database.repositories.compliance_repo import ComplianceRepository
from app.models.compliance_run import Report


class ReportService:
  def __init__(self, db: Session) -> None:
    self.db = db
    self.compliance_repo = ComplianceRepository(db)

  async def generate(self, request: ReportGenerateRequest) -> ReportGenerateResponse:
    """Create report record and dispatch Celery generation task."""
    run = self.compliance_repo.get_by_id(request.run_id)
    if not run:
      raise NotFoundError("ComplianceRun", str(request.run_id))

    report = Report(
      run_id=request.run_id,
      format=request.format.value,
      storage_path="",  # TODO: set after generation
    )
    self.compliance_repo.session.add(report)
    self.compliance_repo.session.commit()

    # TODO: dispatch generate_report_task.delay(report.id, ...)
    return ReportGenerateResponse(
      report_id=report.id,
      status=JobStatus.PENDING.value,
      message="Report generation queued",
    )

  def get_report(self, report_id: UUID) -> ReportResponse:
    report = self.compliance_repo.session.get(Report, report_id)
    if not report:
      raise NotFoundError("Report", str(report_id))
    return ReportResponse.model_validate(report)
