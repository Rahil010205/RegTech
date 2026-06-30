"""Pydantic validation for parsed ingestion payloads."""

from pydantic import BaseModel, Field


class ClausePayload(BaseModel):
  clause_number: str
  title: str | None = None
  text: str = Field(..., min_length=1)
  metadata: dict = Field(default_factory=dict)


class IngestionPayload(BaseModel):
  clauses: list[ClausePayload]
  metadata: dict = Field(default_factory=dict)


class IngestionValidator:
  """Validate parsed ingestion output before persistence."""

  def validate(self, data: dict) -> IngestionPayload:
    return IngestionPayload.model_validate(data)
