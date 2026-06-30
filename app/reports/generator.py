"""Report generation orchestrator."""

from pathlib import Path
from uuid import UUID

from app.reports.json_report import JsonReport
from app.reports.pdf_report import PdfReport


class ReportGenerator:
  """Generate compliance reports in multiple formats."""

  def __init__(self) -> None:
    self.json_report = JsonReport()
    self.pdf_report = PdfReport()

  def generate(self, run_id: UUID, findings: list[dict], fmt: str, output_dir: Path) -> Path:
    """Generate report. Implementation pending."""
    raise NotImplementedError
