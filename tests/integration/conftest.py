"""Shared fixtures for retrieval integration tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import app.models  # noqa: F401
import fitz
import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session, sessionmaker

from app.core.constants import JobStatus
from app.ingestion.embedding_service import EmbeddingService
from app.ingestion.ingestion_pipeline import IngestionOptions, IngestionPipeline
from app.models.clause import Clause, EMBEDDING_DIMENSION
from app.models.regulation import Regulation, RegulationVersion, Regulator


def unit_vector(index: int) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSION
    vector[index] = 1.0
    return vector


def _cleanup_version(session: Session, version_id: UUID, regulation_id: UUID, regulator_code: str) -> None:
    """Remove test ingestion artifacts without touching unrelated data."""
    session.execute(delete(Clause).where(Clause.version_id == version_id))
    session.execute(delete(RegulationVersion).where(RegulationVersion.id == version_id))
    session.execute(delete(Regulation).where(Regulation.id == regulation_id))
    session.execute(delete(Regulator).where(Regulator.code == regulator_code))
    session.commit()


from app.core.config import get_settings


@pytest.fixture
def db_session() -> Session:
    settings = get_settings()
    database_url = settings.database_url
    if not database_url:
        pytest.skip("database_url not set")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def seeded_clauses(db_session: Session) -> dict[str, Any]:
    """Deterministic unit-vector clauses scoped to an isolated test version."""
    suffix = uuid4().hex[:8]
    regulator_code = f"T{suffix[:4].upper()}"
    regulator = Regulator(code=regulator_code, name="Test Regulator", jurisdiction="IN")
    db_session.add(regulator)
    db_session.flush()

    regulation = Regulation(
        regulator_code=regulator.code,
        title="Test Data Retention Regulation",
        document_type="regulation",
    )
    db_session.add(regulation)
    db_session.flush()

    version = RegulationVersion(
        regulation_id=regulation.id,
        version=f"test-{suffix}",
        content_hash=f"hash-{suffix}",
        status=JobStatus.COMPLETED.value,
        is_current=True,
    )
    db_session.add(version)
    db_session.flush()

    retention_clause = Clause(
        version_id=version.id,
        clause_number="4.1",
        section="Data Retention",
        title="Retention period",
        text="The organization shall retain customer records for a minimum period of seven years.",
        page_number=18,
        metadata_={
            "document_name": "RBI_Data_Retention.pdf",
            "regulator": regulator.code,
            "jurisdiction": "IN",
        },
        embedding=unit_vector(0),
    )
    security_clause = Clause(
        version_id=version.id,
        clause_number="5.2",
        section="Security Controls",
        title="Encryption",
        text="All records must use encryption and security controls to prevent unauthorized access.",
        page_number=22,
        metadata_={
            "document_name": "RBI_Data_Retention.pdf",
            "regulator": regulator.code,
            "jurisdiction": "IN",
        },
        embedding=unit_vector(1),
    )
    db_session.add_all([retention_clause, security_clause])
    db_session.commit()

    payload = {
        "regulator": regulator.code,
        "regulation_id": regulation.id,
        "version_id": version.id,
        "retention_clause_id": retention_clause.id,
        "security_clause_id": security_clause.id,
    }
    yield payload
    _cleanup_version(db_session, version.id, regulation.id, regulator.code)


def build_retrieval_eval_pdf(target: Path) -> Path:
    """Create a multi-clause regulatory PDF for real-embedding retrieval tests."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Reserve Bank of India\n"
        "Master Direction - Data Retention and Security\n\n"
        "4.1 Data Retention\n"
        "The organization shall retain customer records for a minimum period of seven years.\n\n"
        "5.2 Security Controls\n"
        "All records must use encryption and security controls to prevent unauthorized access.\n\n"
        "6.3 Encryption Requirements\n"
        "Sensitive customer data at rest and in transit shall be protected using AES-256 encryption.",
    )
    doc.save(target)
    doc.close()
    return target


@pytest.fixture
def real_embedded_document(db_session: Session, tmp_path: Path) -> dict[str, Any]:
    """Ingest a regulatory PDF with real BGE embeddings and clean up afterward."""
    suffix = uuid4().hex[:8]
    regulator_code = f"E{suffix[:4].upper()}"
    pdf_path = build_retrieval_eval_pdf(tmp_path / f"retrieval_eval_{suffix}.pdf")
    version_label = f"reval-{suffix}"
    pipeline = IngestionPipeline(db_session, embedding_service=EmbeddingService())
    result = pipeline.ingest_document(
        pdf_path,
        IngestionOptions(
            regulator_code=regulator_code,
            version=version_label,
            title="RBI Data Retention Eval",
            skip_if_duplicate=False,
            metadata_overrides={"document_name": "RBI_Data_Retention.pdf"},
        ),
    )
    assert result.status == "success"
    assert result.embeddings_created >= 3

    regulation_id = db_session.get(RegulationVersion, result.document_id).regulation_id
    payload = {
        "version_id": result.document_id,
        "regulation_id": regulation_id,
        "regulator": regulator_code,
    }
    yield payload
    _cleanup_version(db_session, result.document_id, regulation_id, regulator_code)
