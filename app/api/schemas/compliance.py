"""Compliance API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import RegulatorCode


class ComplianceEvaluateRequest(BaseModel):
  org_id: UUID
  document_id: UUID
  regulator_codes: list[RegulatorCode] = Field(..., min_length=1)
  regulation_version_ids: list[UUID] | None = None


class ComplianceFindingResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  clause_id: UUID
  status: str
  severity: str
  gap_description: str | None
  evidence: dict


class ComplianceRunResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  org_id: UUID
  document_id: UUID
  status: str
  risk_score: float | None
  compliance_pct: float | None
  created_at: datetime


class ComplianceRunDetailResponse(ComplianceRunResponse):
  findings_count: int = 0


class ComplianceEvaluateResponse(BaseModel):
  run_id: UUID
  status: str
  message: str


class ComplianceFindingsListResponse(BaseModel):
  items: list[ComplianceFindingResponse]
  total: int
