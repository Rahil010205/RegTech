"""Regulatory document ingestion pipeline."""

from app.ingestion.embedding_service import EmbeddingService
from app.ingestion.ingestion_pipeline import (
    IngestionOptions,
    IngestionPipeline,
    IngestionResult,
    ingest_document,
)

__all__ = [
    "EmbeddingService",
    "IngestionOptions",
    "IngestionPipeline",
    "IngestionResult",
    "ingest_document",
]
