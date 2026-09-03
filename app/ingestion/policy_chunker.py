"""Policy-aware chunking that reuses regulatory clause splitting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from loguru import logger

from app.ingestion.clause_splitter import ClauseRecord, ClauseSplitter
from app.ingestion.pdf_loader import PageContent


@dataclass(frozen=True)
class PolicyChunk:
    """A retrieval-ready organization policy chunk."""

    chunk_index: int
    content: str
    section_title: str | None
    clause_reference: str | None
    page_number: int | None
    page_end: int | None
    metadata: dict[str, Any]


class PolicyChunker:
    """Chunk organization policies while preserving sections and clause numbers.

    Reuses :class:`ClauseSplitter` so numbered requirements, headings, and
    subclauses stay together. Consecutive fragments that share a clause
    identifier are merged rather than stored as duplicate records.
    """

    def __init__(self, splitter: ClauseSplitter | None = None) -> None:
        self._splitter = splitter or ClauseSplitter()

    def chunk_pages(
        self,
        pages: list[PageContent],
        *,
        document_type: str | None = None,
        document_name: str | None = None,
        version: str | None = None,
    ) -> list[PolicyChunk]:
        records = self._splitter.split_pages(pages)
        merged = self._merge_duplicate_clause_numbers(records)
        chunks: list[PolicyChunk] = []
        for index, record in enumerate(merged):
            content = (record.get("text") or "").strip()
            if not content:
                continue
            section_title = (record.get("section") or record.get("title") or "").strip() or None
            clause_reference = (record.get("clause_number") or "").strip() or None
            if clause_reference == "0":
                clause_reference = None
            chunks.append(
                PolicyChunk(
                    chunk_index=index,
                    content=content,
                    section_title=section_title,
                    clause_reference=clause_reference,
                    page_number=record.get("page_number"),
                    page_end=record.get("page_end"),
                    metadata={
                        "section_title": section_title,
                        "clause_reference": clause_reference,
                        "chunk_index": index,
                        "document_type": document_type,
                        "document_name": document_name,
                        "version": version,
                        "page_number": record.get("page_number"),
                        "page_end": record.get("page_end"),
                    },
                )
            )
        logger.info("Policy chunker produced {} chunk(s)", len(chunks))
        return chunks

    @staticmethod
    def _merge_duplicate_clause_numbers(records: list[ClauseRecord]) -> list[ClauseRecord]:
        merged: list[ClauseRecord] = []
        index_by_number: dict[str, int] = {}
        for record in records:
            number = record["clause_number"]
            if number in index_by_number:
                existing = merged[index_by_number[number]]
                existing["text"] = f"{existing['text'].rstrip()} {record['text'].strip()}".strip()
                if record.get("page_end") is not None:
                    existing["page_end"] = record["page_end"]
                continue
            index_by_number[number] = len(merged)
            merged.append(dict(record))  # type: ignore[arg-type]
        return merged
