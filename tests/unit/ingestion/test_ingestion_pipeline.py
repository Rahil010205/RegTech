"""Tests for regulatory ingestion pipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import fitz
import pytest

from app.core.constants import JobStatus
from app.core.exceptions import EmptyDocumentError
from app.ingestion.embedding_service import EmbeddingService
from app.ingestion.ingestion_pipeline import IngestionOptions, IngestionPipeline


class _FakeEmbeddingService(EmbeddingService):
    def __init__(self) -> None:
        pass

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]

    @property
    def embedding_dimension(self) -> int:
        return 4


@pytest.fixture
def sample_regulatory_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "sample_regulation.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Reserve Bank of India\n"
        "Master Direction - Data Retention\n"
        "Section 4 — Data Retention\n"
        "4.1 The organization shall retain customer records for a minimum period of seven years.\n"
        "4.2 Records must be protected against unauthorized modification.",
    )
    doc.save(pdf_path)
    doc.close()
    return pdf_path


class TestIngestionPipelineUnit:
    def test_rejects_missing_file(self) -> None:
        session = MagicMock()
        pipeline = IngestionPipeline(session, embedding_service=_FakeEmbeddingService())
        with pytest.raises(Exception):
            pipeline.ingest_document(Path("missing.pdf"))

    def test_rejects_empty_pdf(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "empty.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(pdf_path)
        doc.close()

        session = MagicMock()
        pipeline = IngestionPipeline(session, embedding_service=_FakeEmbeddingService())
        with pytest.raises(EmptyDocumentError):
            pipeline.ingest_document(pdf_path)

    @patch("app.ingestion.ingestion_pipeline.ClauseRepository")
    @patch("app.ingestion.ingestion_pipeline.RegulationIngestionRepository")
    def test_duplicate_completed_document_short_circuits(
        self,
        repo_cls: MagicMock,
        clause_repo_cls: MagicMock,
        sample_regulatory_pdf: Path,
    ) -> None:
        session = MagicMock()
        existing = MagicMock()
        existing.id = uuid4()
        existing.regulation_id = uuid4()
        existing.status = JobStatus.COMPLETED.value
        repo = repo_cls.return_value
        repo.get_version_by_content_hash.return_value = existing
        clause_repo_cls.return_value.count_by_version.return_value = 2

        pipeline = IngestionPipeline(session, embedding_service=_FakeEmbeddingService())
        result = pipeline.ingest_document(
            sample_regulatory_pdf,
            IngestionOptions(skip_if_duplicate=True),
        )
        assert result.duplicate is True
        assert result.clauses_created == 2
        session.commit.assert_not_called()
