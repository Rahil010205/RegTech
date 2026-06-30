"""Shared ingestion orchestration for regulatory and org documents."""

from pathlib import Path

from sqlalchemy.orm import Session

from app.ingestion.clause_splitter import ClauseSplitter
from app.ingestion.metadata_extractor import MetadataExtractor
from app.ingestion.pdf_loader import PdfLoader
from app.ingestion.text_cleaner import TextCleaner
from app.ingestion.validator import IngestionValidator


class IngestionService:
  """Orchestrates the PDF → clauses pipeline."""

  def __init__(self, db: Session) -> None:
    self.db = db
    self.pdf_loader = PdfLoader()
    self.text_cleaner = TextCleaner()
    self.clause_splitter = ClauseSplitter()
    self.metadata_extractor = MetadataExtractor()
    self.validator = IngestionValidator()

  def ingest_file(self, file_path: Path) -> dict:
    """Run full ingestion pipeline. Implementation pending."""
    raise NotImplementedError
