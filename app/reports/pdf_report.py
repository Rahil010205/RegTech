"""PDF compliance report generator."""

from pathlib import Path
from uuid import UUID


class PdfReport:
  def generate(self, run_id: UUID, findings: list[dict], output_path: Path) -> Path:
    """Generate PDF report. Implementation pending."""
    raise NotImplementedError
