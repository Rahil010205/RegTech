"""Shared ingestion orchestration for regulatory and org documents."""

from pathlib import Path

from sqlalchemy.orm import Session

from app.ingestion.ingestion_pipeline import IngestionOptions, IngestionPipeline, IngestionResult


class IngestionService:
    """Application service wrapper around the regulatory ingestion pipeline."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.pipeline = IngestionPipeline(db)

    def ingest_file(
        self,
        file_path: Path,
        *,
        regulator_code: str = "RBI",
        version: str = "1.0",
        title: str | None = None,
        document_type: str = "regulation",
    ) -> IngestionResult:
        """Run the regulatory ingestion pipeline for a local PDF."""
        options = IngestionOptions(
            regulator_code=regulator_code,
            version=version,
            title=title,
            document_type=document_type,
        )
        return self.pipeline.ingest_document(file_path, options)
