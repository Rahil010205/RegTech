"""Report generation port."""

from pathlib import Path
from typing import Any, Protocol
from uuid import UUID


class ReportPort(Protocol):
  """Abstract interface for compliance report generation."""

  def generate_json(self, run_id: UUID, findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate a structured JSON compliance report."""
    ...

  def generate_pdf(self, run_id: UUID, findings: list[dict[str, Any]], output_path: Path) -> Path:
    """Generate a PDF compliance report."""
    ...
