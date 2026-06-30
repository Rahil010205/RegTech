"""Regulation domain entity."""

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID


@dataclass
class Regulation:
  id: UUID
  regulator_code: str
  title: str
  document_type: str
  created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RegulationVersion:
  id: UUID
  regulation_id: UUID
  version: str
  effective_date: date | None
  is_current: bool
  content_hash: str
  status: str
