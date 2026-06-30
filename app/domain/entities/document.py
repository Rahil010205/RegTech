"""Organization document domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class Document:
  id: UUID
  org_id: UUID
  filename: str
  doc_type: str
  status: str
  content_hash: str
  created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DocumentSection:
  id: UUID
  document_id: UUID
  section_number: str
  text: str
