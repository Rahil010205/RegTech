"""Integration tests for ingestion pipeline (requires PostgreSQL + pgvector)."""

from __future__ import annotations

import os
from pathlib import Path

import app.models  # noqa: F401 — register all ORM mappers
import fitz
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.ingestion.embedding_service import EmbeddingService
from app.ingestion.ingestion_pipeline import IngestionOptions, IngestionPipeline


class _FakeEmbeddingService(EmbeddingService):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.01] * 1024 for _ in texts]

    @property
    def embedding_dimension(self) -> int:
        return 1024


from app.core.config import get_settings


@pytest.fixture
def db_session():
    settings = get_settings()
    database_url = settings.database_url
    if not database_url:
        pytest.skip("database_url not set — skipping integration test")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def regulatory_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "integration_regulation.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Reserve Bank of India\n"
        "Master Direction - Data Retention\n"
        "4.1 The organization shall retain customer records for seven years.\n"
        "4.2 Records must be protected against unauthorized modification.",
    )
    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.mark.integration
def test_full_ingestion_persists_clauses_and_embeddings(db_session, regulatory_pdf: Path) -> None:
    from sqlalchemy import delete

    from app.models.clause import Clause
    from app.models.regulation import Regulation, RegulationVersion, Regulator

    pipeline = IngestionPipeline(db_session, embedding_service=_FakeEmbeddingService())
    version_label = f"itest-{regulatory_pdf.stat().st_mtime_ns}"
    result = pipeline.ingest_document(
        regulatory_pdf,
        IngestionOptions(
            regulator_code="I999",
            version=version_label,
            skip_if_duplicate=False,
        ),
    )

    try:
        assert result.status == "success"
        assert result.clauses_created >= 1
        assert result.embeddings_created == result.clauses_created

        row = db_session.execute(
            text(
                """
                SELECT COUNT(*) AS clause_count
                FROM clauses
                WHERE version_id = :version_id
                """
            ),
            {"version_id": str(result.document_id)},
        ).one()
        assert row.clause_count == result.clauses_created

        embedding_row = db_session.execute(
            text(
                """
                SELECT vector_dims(embedding) AS dims
                FROM clauses
                WHERE version_id = :version_id
                LIMIT 1
                """
            ),
            {"version_id": str(result.document_id)},
        ).one()
        assert embedding_row.dims == 1024
    finally:
        version = db_session.get(RegulationVersion, result.document_id)
        regulation_id = version.regulation_id if version else None
        db_session.execute(delete(Clause).where(Clause.version_id == result.document_id))
        db_session.execute(delete(RegulationVersion).where(RegulationVersion.id == result.document_id))
        if regulation_id is not None:
            db_session.execute(delete(Regulation).where(Regulation.id == regulation_id))
        db_session.execute(delete(Regulator).where(Regulator.code == "I999"))
        db_session.commit()
