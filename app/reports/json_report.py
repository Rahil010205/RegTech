"""JSON compliance report generator."""

from uuid import UUID


class JsonReport:
  def generate(self, run_id: UUID, findings: list[dict]) -> dict:
    """Generate structured JSON report. Implementation pending."""
    raise NotImplementedError
