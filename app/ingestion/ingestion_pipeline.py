"""Regulatory document ingestion pipeline.

Orchestrates:
    PDF → extract → clean → split → metadata → embed → PostgreSQL/pgvector
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import JobStatus
from app.core.exceptions import (
    DatabaseError,
    DuplicateDocumentError,
    EmptyDocumentError,
    EmbeddingModelError,
    IngestionError,
)
from app.database.repositories.clause_repo import ClauseRepository
from app.database.repositories.regulation_ingestion_repo import RegulationIngestionRepository
from app.ingestion.clause_splitter import ClauseSplitter
from app.ingestion.embedding_service import EmbeddingService
from app.ingestion.metadata_extractor import MetadataExtractor
from app.ingestion.pdf_loader import PDFLoader, PDFLoaderError
from app.ingestion.text_cleaner import TextCleaner
import app.models  # noqa: F401 — register all ORM mappers
from app.models.clause import Clause
from app.models.regulation import RegulationVersion
from app.utils.file_utils import ensure_dir
from app.utils.hash_utils import hash_file

_JURISDICTION_NAMES = {
    "RBI": ("Reserve Bank of India", "IN"),
    "SEBI": ("Securities and Exchange Board of India", "IN"),
    "IRDAI": ("Insurance Regulatory and Development Authority of India", "IN"),
    "GDPR": ("General Data Protection Regulation", "EU"),
    "ISO": ("International Organization for Standardization", "GLOBAL"),
    "PCI_DSS": ("Payment Card Industry Data Security Standard", "GLOBAL"),
}


@dataclass(frozen=True)
class IngestionOptions:
    """Optional overrides for regulatory ingestion."""

    regulator_code: str = "RBI"
    version: str = "1.0"
    title: str | None = None
    document_type: str = "regulation"
    metadata_overrides: dict[str, Any] = field(default_factory=dict)
    skip_if_duplicate: bool = True


@dataclass(frozen=True)
class IngestionResult:
    """Summary returned after ingestion completes."""

    document_id: UUID
    regulation_id: UUID
    document_name: str
    pages_processed: int
    clauses_created: int
    embeddings_created: int
    status: str
    duplicate: bool = False
    message: str = ""


class IngestionPipeline:
    """End-to-end regulatory document ingestion pipeline."""

    def __init__(
        self,
        session: Session,
        *,
        embedding_service: EmbeddingService | None = None,
        pdf_loader_cls: type[PDFLoader] = PDFLoader,
        text_cleaner: TextCleaner | None = None,
        clause_splitter: ClauseSplitter | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        raw_data_dir: Path | None = None,
    ) -> None:
        self.session = session
        self.embedding_service = embedding_service or EmbeddingService()
        self.pdf_loader_cls = pdf_loader_cls
        self.text_cleaner = text_cleaner or TextCleaner()
        self.clause_splitter = clause_splitter or ClauseSplitter()
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        self.regulation_repo = RegulationIngestionRepository(session)
        self.clause_repo = ClauseRepository(session)
        self.raw_data_dir = raw_data_dir

    def ingest_document(self, file_path: Path, options: IngestionOptions | None = None) -> IngestionResult:
        """Ingest a regulatory PDF and persist clauses with pgvector embeddings."""
        opts = options or IngestionOptions()
        path = Path(file_path)
        self._validate_file(path)

        content_hash = hash_file(path)
        existing = self.regulation_repo.get_version_by_content_hash(content_hash)
        if existing and existing.status == JobStatus.COMPLETED.value and opts.skip_if_duplicate:
            clause_count = self.clause_repo.count_by_version(existing.id)
            logger.info(
                "Duplicate document detected — content_hash={} version_id={}",
                content_hash,
                existing.id,
            )
            return IngestionResult(
                document_id=existing.id,
                regulation_id=existing.regulation_id,
                document_name=path.name,
                pages_processed=0,
                clauses_created=clause_count,
                embeddings_created=clause_count,
                status="success",
                duplicate=True,
                message="Document already ingested; returning existing record",
            )

        version_row: RegulationVersion | None = existing
        try:
            loader = self.pdf_loader_cls(path)
            pages = loader.load_pdf()
            pdf_meta = loader.get_metadata()

            if not pages or all(not page["text"].strip() for page in pages):
                raise EmptyDocumentError(f"PDF '{path.name}' contains no extractable text")

            cleaned_pages = self.text_cleaner.clean_pages(pages)
            clause_records = self.clause_splitter.split_pages(cleaned_pages)
            if not clause_records:
                raise IngestionError(
                    "No clauses detected in document after splitting",
                    "CLAUSE_SPLITTING_FAILED",
                )

            clean_doc = self.text_cleaner.clean_document(cleaned_pages)
            doc_metadata = self.metadata_extractor.extract(clean_doc, path.name)
            doc_metadata["total_pages"] = pdf_meta["total_pages"]
            doc_metadata = self._apply_overrides(doc_metadata, opts)

            regulator_code = opts.regulator_code or doc_metadata.get("regulator") or "RBI"
            regulator_name, jurisdiction = _JURISDICTION_NAMES.get(
                regulator_code,
                (regulator_code, doc_metadata.get("jurisdiction") or "GLOBAL"),
            )
            self.regulation_repo.ensure_regulator(regulator_code, regulator_name, jurisdiction)

            stored_path = self._store_source_file(path, content_hash)
            title = opts.title or doc_metadata.get("document_name") or path.stem
            document_type = opts.document_type or doc_metadata.get("document_type") or "regulation"
            effective_date = self.metadata_extractor.parse_effective_date(
                doc_metadata.get("effective_date")
            )

            if version_row is not None:
                self.clause_repo.delete_by_version(version_row.id)
                version_row.storage_path = str(stored_path)
                version_row.status = JobStatus.PROCESSING.value
                self.session.flush()
            else:
                regulation = self.regulation_repo.create_regulation(
                    regulator_code=regulator_code,
                    title=title[:500],
                    document_type=document_type[:50],
                )
                version_row = self.regulation_repo.create_version(
                    regulation_id=regulation.id,
                    version=opts.version,
                    content_hash=content_hash,
                    effective_date=effective_date,
                    storage_path=str(stored_path),
                    status=JobStatus.PROCESSING.value,
                )

            self.regulation_repo.mark_current(version_row)
            document_id = version_row.id

            clause_texts = [record["text"] for record in clause_records]
            embeddings = self._embed_in_batches(clause_texts)

            clause_models: list[Clause] = []
            for record, embedding in zip(clause_records, embeddings, strict=True):
                clause_meta = self.metadata_extractor.enrich_clause(
                    record,
                    doc_metadata,
                    document_id=str(document_id),
                )
                clause_models.append(
                    Clause(
                        version_id=document_id,
                        clause_number=record["clause_number"],
                        section=record.get("section") or doc_metadata.get("section"),
                        title=record.get("title") or None,
                        text=record["text"],
                        page_number=record.get("page_number"),
                        page_end=record.get("page_end"),
                        metadata_=clause_meta,
                        embedding=embedding,
                    )
                )

            self.clause_repo.bulk_create(clause_models)
            self.regulation_repo.update_status(version_row, JobStatus.COMPLETED.value)
            self.session.commit()

            logger.info(
                "Ingestion complete — document_id={} clauses={}",
                document_id,
                len(clause_models),
            )
            return IngestionResult(
                document_id=document_id,
                regulation_id=version_row.regulation_id,
                document_name=path.name,
                pages_processed=pdf_meta["total_pages"],
                clauses_created=len(clause_models),
                embeddings_created=len(embeddings),
                status="success",
                message="Document ingested successfully",
            )
        except (PDFLoaderError, EmptyDocumentError, IngestionError, EmbeddingModelError):
            self.session.rollback()
            raise
        except Exception as exc:
            self.session.rollback()
            if version_row is not None:
                try:
                    self.regulation_repo.update_status(version_row, JobStatus.FAILED.value)
                    self.session.commit()
                except Exception:
                    self.session.rollback()
            logger.exception("Ingestion failed for {}", path)
            raise DatabaseError(f"Ingestion failed: {exc}") from exc

    def _validate_file(self, path: Path) -> None:
        if not path.exists():
            raise IngestionError(f"File not found: {path}", "FILE_NOT_FOUND")
        if path.suffix.lower() != ".pdf":
            raise IngestionError(f"Unsupported file type: {path.suffix}", "INVALID_FILE_TYPE")

    def _apply_overrides(self, metadata: dict[str, Any], opts: IngestionOptions) -> dict[str, Any]:
        merged = dict(metadata)
        merged.update({k: v for k, v in opts.metadata_overrides.items() if v is not None})
        if opts.regulator_code:
            merged["regulator"] = opts.regulator_code
        if opts.title:
            merged["document_name"] = opts.title
        if opts.document_type:
            merged["document_type"] = opts.document_type
        if opts.version:
            merged["version"] = opts.version
        return merged

    def _store_source_file(self, source: Path, content_hash: str) -> Path:
        settings = get_settings()
        target_dir = self.raw_data_dir or settings.raw_data_dir
        ensure_dir(target_dir)
        target = target_dir / f"{content_hash[:16]}_{source.name}"
        if not target.exists():
            shutil.copy2(source, target)
        return target

    def _embed_in_batches(self, texts: list[str]) -> list[list[float]]:
        batch_size = max(1, get_settings().embedding_batch_size)
        all_vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            all_vectors.extend(self.embedding_service.embed_texts(batch))
        if len(all_vectors) != len(texts):
            raise EmbeddingModelError("Embedding count does not match clause count")
        return all_vectors


def ingest_document(
    file_path: Path | str,
    session: Session,
    options: IngestionOptions | None = None,
) -> IngestionResult:
    """Functional entry point used by services and CLI."""
    pipeline = IngestionPipeline(session)
    return pipeline.ingest_document(Path(file_path), options)


def main() -> None:
    """CLI entry point: python -m app.ingestion.ingestion_pipeline <pdf> [options]."""
    import argparse

    from app.database.session import SessionLocal

    parser = argparse.ArgumentParser(description="Ingest a regulatory PDF into PostgreSQL/pgvector")
    parser.add_argument("pdf", type=Path, help="Path to regulatory PDF")
    parser.add_argument("--regulator", default="RBI", help="Regulator code (RBI, SEBI, GDPR, etc.)")
    parser.add_argument("--version", default="1.0", help="Document version label")
    parser.add_argument("--title", default=None, help="Override document title")
    parser.add_argument("--document-type", default="regulation", help="Document type")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-ingest even if the same content hash already exists",
    )
    args = parser.parse_args()

    options = IngestionOptions(
        regulator_code=args.regulator,
        version=args.version,
        title=args.title,
        document_type=args.document_type,
        skip_if_duplicate=not args.force,
    )

    with SessionLocal() as session:
        result = ingest_document(args.pdf, session, options)

    print(
        {
            "document_id": str(result.document_id),
            "document_name": result.document_name,
            "pages_processed": result.pages_processed,
            "clauses_created": result.clauses_created,
            "embeddings_created": result.embeddings_created,
            "status": result.status,
            "duplicate": result.duplicate,
            "message": result.message,
        }
    )


if __name__ == "__main__":
    main()
