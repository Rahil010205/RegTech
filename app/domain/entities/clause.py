"""Clause domain entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class Clause:
  id: UUID
  version_id: UUID
  clause_number: str
  title: str | None
  text: str
  qdrant_point_id: UUID | None
  metadata: dict
