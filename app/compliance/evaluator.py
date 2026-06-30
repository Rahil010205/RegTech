"""Compliance evaluation orchestrator."""

from uuid import UUID

from app.compliance.comparator import Comparator
from app.compliance.rule_engine import RuleEngine
from app.compliance.scorer import Scorer
from app.retrieval.retriever import Retriever


class ComplianceEvaluator:
  """Evaluate org document sections against regulatory clauses."""

  def __init__(self) -> None:
    self.retriever = Retriever()
    self.comparator = Comparator()
    self.rule_engine = RuleEngine()
    self.scorer = Scorer()

  def evaluate(self, document_id: UUID, regulator_codes: list[str]) -> dict:
    """Run full evaluation. Implementation pending."""
    raise NotImplementedError
