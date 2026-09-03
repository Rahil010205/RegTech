"""Unit tests for organization policy ingestion pipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import fitz
import pytest

from app.core.config import Settings
from app.core.constants import OrganizationDocumentStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.ingestion.embedding_service import EmbeddingService
from app.ingestion.organization_policy_pipeline import OrganizationPolicyPipeline
from app.models.clause import EMBEDDING_DIMENSION
from app.models.organization import Organization
from app.models.organization_document import OrganizationDocument


class _FakeEmbeddingService(EmbeddingService):
    def __init__(self) -> None:
        pass

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.01] * EMBEDDING_DIMENSION for _ in texts]

    @property
    def embedding_dimension(self) -> int:
        return EMBEDDING_DIMENSION


def _policy_pdf(tmp_path: Path) -> bytes:
    pdf_path = tmp_path / "company_kyc_policy.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Customer Due Diligence\n"
        "1. The organization shall conduct customer due diligence before onboarding.\n"
        "2. The organization shall verify identity using reliable documents.\n",
    )
    doc.save(pdf_path)
    doc.close()
    return pdf_path.read_bytes()


def _session_with_org(organization_id: UUID | None = None) -> MagicMock:
    org_id = organization_id or uuid4()
    org = Organization(name="Acme", slug="acme")
    org.id = org_id
    added: list[object] = []
    session = MagicMock()

    def add(obj: object) -> None:
        added.append(obj)

    def get(model: type, ident: UUID) -> object | None:
        if model is Organization:
            return org
        if model is OrganizationDocument:
            for obj in added:
                if isinstance(obj, OrganizationDocument) and obj.id == ident:
                    return obj
        return None

    session.add.side_effect = add
    session.get.side_effect = get
    session._added = added
    return session


def _pipeline(session: MagicMock | None = None) -> OrganizationPolicyPipeline:
    return OrganizationPolicyPipeline(
        session or _session_with_org(),
        embedding_service=_FakeEmbeddingService(),
        settings=Settings(max_upload_bytes=1024 * 1024),
    )


def test_rejects_unsupported_extension() -> None:
    pipeline = _pipeline()
    with pytest.raises(ValidationError):
        pipeline.ingest_upload(
            organization_id=uuid4(),
            filename="notes.txt",
            content=b"not a pdf",
        )


def test_rejects_empty_file() -> None:
    pipeline = _pipeline()
    with pytest.raises(ValidationError, match="empty"):
        pipeline.ingest_upload(
            organization_id=uuid4(),
            filename="empty.pdf",
            content=b"",
        )


def test_rejects_missing_organization() -> None:
    session = MagicMock()
    session.get.return_value = None
    pipeline = _pipeline(session)
    with pytest.raises(NotFoundError):
        pipeline.ingest_upload(
            organization_id=uuid4(),
            filename="policy.pdf",
            content=b"%PDF-1.4",
        )


def test_rejects_oversized_file() -> None:
    pipeline = OrganizationPolicyPipeline(
        _session_with_org(),
        embedding_service=_FakeEmbeddingService(),
        settings=Settings(max_upload_bytes=10),
    )
    with pytest.raises(ValidationError, match="maximum size"):
        pipeline.ingest_upload(
            organization_id=uuid4(),
            filename="policy.pdf",
            content=b"%PDF-1.4 oversized",
        )


def test_sanitizes_path_traversal_filename(tmp_path: Path) -> None:
    pipeline = _pipeline()
    result = pipeline.ingest_upload(
        organization_id=uuid4(),
        filename="../../etc/company_kyc_policy.pdf",
        content=_policy_pdf(tmp_path),
    )
    assert result.document_name == "company_kyc_policy.pdf"
    assert result.status == OrganizationDocumentStatus.PROCESSED.value
    assert result.chunks_created >= 1


def test_successful_ingest_creates_chunks_and_embeddings(tmp_path: Path) -> None:
    session = _session_with_org()
    pipeline = _pipeline(session)
    result = pipeline.ingest_upload(
        organization_id=uuid4(),
        filename="company_kyc_policy.pdf",
        content=_policy_pdf(tmp_path),
        document_type="KYC_POLICY",
        version="2026.1",
    )
    assert result.status == OrganizationDocumentStatus.PROCESSED.value
    assert result.chunks_created >= 1
    session.add_all.assert_called()
    assert session.commit.call_count >= 2
    added_chunks = session.add_all.call_args[0][0]
    assert all(len(chunk.embedding) == EMBEDDING_DIMENSION for chunk in added_chunks)
    assert all(chunk.content.strip() for chunk in added_chunks)


def test_empty_pdf_marks_document_failed(tmp_path: Path) -> None:
    session = _session_with_org()
    pipeline = _pipeline(session)

    pdf_path = tmp_path / "blank.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(pdf_path)
    doc.close()

    result = pipeline.ingest_upload(
        organization_id=uuid4(),
        filename="blank.pdf",
        content=pdf_path.read_bytes(),
    )
    assert result.status == OrganizationDocumentStatus.FAILED.value
    assert result.error
    session.rollback.assert_called()
    document = next(obj for obj in session._added if isinstance(obj, OrganizationDocument))
    assert document.status == OrganizationDocumentStatus.FAILED.value


def test_corrupt_pdf_is_rejected_or_failed() -> None:
    pipeline = _pipeline()
    with pytest.raises(ValidationError, match="not a valid PDF"):
        pipeline.ingest_upload(
            organization_id=uuid4(),
            filename="corrupt.pdf",
            content=b"this is not a pdf",
        )
