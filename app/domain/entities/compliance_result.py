"""Compliance evaluation result domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class ComplianceRun:
  id: UUID
  org_id: UUID
  document_id: UUID
  status: str
  risk_score: float | None = None
  compliance_pct: float | None = None
  created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ComplianceFinding:
  id: UUID
  run_id: UUID
  clause_id: UUID
  status: str
  severity: str
  gap_description: str | None
  evidence: dict = field(default_factory=dict)
