"""Organization policy document ingestion pipeline."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.constants import OrganizationDocumentStatus
from app.core.exceptions import EmptyDocumentError, IngestionError, NotFoundError, ValidationError
from app.ingestion.embedding_service import EmbeddingService
from app.ingestion.pdf_loader import InvalidPDFError, PDFLoader, PDFLoaderError, PDFOpenError
from app.ingestion.policy_chunker import PolicyChunk, PolicyChunker
from app.ingestion.text_cleaner import TextCleaner
from app.models.organization import Organization
from app.models.organization_document import OrganizationDocument
from app.models.organization_policy_chunk import OrganizationPolicyChunk


@dataclass(frozen=True)
class OrganizationPolicyIngestResult:
    """Outcome of organization policy ingestion."""

    document_id: UUID
    organization_id: UUID
    document_name: str
    status: str
    chunks_created: int = 0
    error: str | None = None


class OrganizationPolicyPipeline:
    """Extract, chunk, embed, and store organization policy documents.

    The original PDF is processed from a temporary file and is not persisted
    in PostgreSQL.
    """

    def __init__(
        self,
        session: Session,
        *,
        embedding_service: EmbeddingService | None = None,
        text_cleaner: TextCleaner | None = None,
        chunker: PolicyChunker | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.session = session
        self.embedding_service = embedding_service or EmbeddingService()
        self.text_cleaner = text_cleaner or TextCleaner()
        self.chunker = chunker or PolicyChunker()
        self.settings = settings or get_settings()

    def ingest_upload(
        self,
        *,
        organization_id: UUID,
        filename: str,
        content: bytes,
        document_type: str | None = None,
        version: str | None = None,
    ) -> OrganizationPolicyIngestResult:
        organization = self.session.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError("Organization", str(organization_id))

        safe_name = self._safe_filename(filename)
        self._validate_upload(safe_name, content)

        document = OrganizationDocument(
            id=uuid4(),
            organization_id=organization_id,
            document_name=safe_name,
            document_type=document_type,
            source_filename=safe_name,
            version=version,
            status=OrganizationDocumentStatus.PROCESSING.value,
        )
        self.session.add(document)
        self.session.commit()
        document_id = document.id
        logger.info(
            "Organization document upload started — document_id={} organization_id={}",
            document_id,
            organization_id,
        )

        try:
            document = self.session.get(OrganizationDocument, document_id)
            if document is None:
                raise IngestionError("Organization document record was not persisted")
            chunks_created = self._process_document(
                document,
                content=content,
                document_type=document_type,
                version=version,
            )
            document.status = OrganizationDocumentStatus.PROCESSED.value
            document.error_message = None
            self.session.commit()
            logger.info(
                "Organization document processing completed — document_id={} chunks={}",
                document_id,
                chunks_created,
            )
            return OrganizationPolicyIngestResult(
                document_id=document_id,
                organization_id=organization_id,
                document_name=safe_name,
                status=OrganizationDocumentStatus.PROCESSED.value,
                chunks_created=chunks_created,
            )
        except Exception as exc:
            logger.exception(
                "Organization document ingestion failed — document_id={}",
                document_id,
            )
            self.session.rollback()
            self._mark_failed(document_id, str(exc))
            return OrganizationPolicyIngestResult(
                document_id=document_id,
                organization_id=organization_id,
                document_name=safe_name,
                status=OrganizationDocumentStatus.FAILED.value,
                chunks_created=0,
                error=self._public_error(exc),
            )

    def ingest_file(
        self,
        *,
        organization_id: UUID,
        file_path: Path,
        document_type: str | None = None,
        version: str | None = None,
    ) -> OrganizationPolicyIngestResult:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise ValidationError(f"File not found: {path}")
        content = path.read_bytes()
        return self.ingest_upload(
            organization_id=organization_id,
            filename=path.name,
            content=content,
            document_type=document_type,
            version=version,
        )

    def _process_document(
        self,
        document: OrganizationDocument,
        *,
        content: bytes,
        document_type: str | None,
        version: str | None,
    ) -> int:
        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            loader = PDFLoader(tmp_path)
            pages = loader.load_pdf()
        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)

        extracted_chars = sum(len(page["text"]) for page in pages)
        logger.info(
            "PDF extraction completed — document_id={} characters={}",
            document.id,
            extracted_chars,
        )
        if extracted_chars == 0 or all(not page["text"].strip() for page in pages):
            raise EmptyDocumentError("Uploaded PDF contains no extractable text")

        cleaned_pages = self.text_cleaner.clean_pages(pages)
        policy_chunks = self.chunker.chunk_pages(
            cleaned_pages,
            document_type=document_type,
            document_name=document.document_name,
            version=version,
        )
        if not policy_chunks:
            raise IngestionError("No policy chunks could be extracted from the document")

        logger.info("Created {} policy chunks — document_id={}", len(policy_chunks), document.id)
        embeddings = self._embed_chunks(policy_chunks)
        logger.info("Generated {} embeddings — document_id={}", len(embeddings), document.id)

        models = [
            OrganizationPolicyChunk(
                document_id=document.id,
                organization_id=document.organization_id,
                chunk_index=chunk.chunk_index,
                section_title=chunk.section_title,
                clause_reference=chunk.clause_reference,
                content=chunk.content,
                embedding=vector,
                metadata_=chunk.metadata,
            )
            for chunk, vector in zip(policy_chunks, embeddings, strict=True)
        ]
        self.session.add_all(models)
        self.session.flush()
        logger.info("Inserted {} policy chunks — document_id={}", len(models), document.id)
        return len(models)

    def _embed_chunks(self, chunks: list[PolicyChunk]) -> list[list[float]]:
        batch_size = max(1, self.settings.embedding_batch_size)
        texts = [chunk.content for chunk in chunks]
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            vectors.extend(self.embedding_service.embed_texts(batch))
        if len(vectors) != len(chunks):
            raise IngestionError("Embedding count does not match policy chunk count")
        return vectors

    def _mark_failed(self, document_id: UUID, error: str) -> None:
        failed = self.session.get(OrganizationDocument, document_id)
        if failed is None:
            return
        failed.status = OrganizationDocumentStatus.FAILED.value
        failed.error_message = error[:2000]
        self.session.commit()

    def _validate_upload(self, filename: str, content: bytes) -> None:
        if not filename.lower().endswith(".pdf"):
            raise ValidationError(
                "Unsupported file type. Only PDF uploads are accepted.",
                details={"filename": filename},
            )
        if not content:
            raise ValidationError("Uploaded file is empty")
        max_bytes = self.settings.max_upload_bytes
        if len(content) > max_bytes:
            raise ValidationError(
                f"Uploaded file exceeds the maximum size of {max_bytes} bytes",
                details={"size": len(content), "max_bytes": max_bytes},
            )
        if not content.startswith(b"%PDF"):
            raise ValidationError("Uploaded file is not a valid PDF")

    @staticmethod
    def _safe_filename(filename: str) -> str:
        name = Path(filename or "").name.strip()
        if not name or name in {".", ".."}:
            return "upload.pdf"
        return name

    @staticmethod
    def _public_error(exc: Exception) -> str:
        if isinstance(exc, (ValidationError, EmptyDocumentError, IngestionError, PDFLoaderError, InvalidPDFError, PDFOpenError)):
            return str(exc)
        return "Organization document ingestion failed"
