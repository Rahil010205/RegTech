"""Risk and compliance scoring."""


class Scorer:
  """Aggregate per-section scores into run-level risk and compliance metrics."""

  def score(self, findings: list[dict]) -> dict:
    """Return risk_score and compliance_pct. Implementation pending."""
    raise NotImplementedError
