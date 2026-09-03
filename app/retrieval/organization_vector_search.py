"""pgvector similarity search for organization policy chunks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy import bindparam, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import Vector

from app.core.exceptions import DatabaseError
from app.models.clause import EMBEDDING_DIMENSION


@dataclass(frozen=True)
class OrganizationPolicySearchRow:
    chunk_id: UUID
    document_id: UUID
    document_name: str | None
    content: str
    section_title: str | None
    clause_reference: str | None
    similarity: float
    metadata: dict[str, Any]
    document_type: str | None = None
    document_version: str | None = None


class OrganizationPolicyVectorSearch:
    """Search organization policy embeddings, scoped by organization."""

    _QUERY = """
        SELECT
            c.id AS chunk_id,
            c.document_id,
            d.document_name,
            c.content,
            c.section_title,
            c.clause_reference,
            c.metadata,
            d.document_type,
            d.version AS document_version,
            1 - (c.embedding <=> :query_embedding) AS similarity
        FROM organization_policy_chunks c
        INNER JOIN organization_documents d ON d.id = c.document_id
        WHERE c.organization_id = :organization_id
          AND d.organization_id = :organization_id
          AND d.status = 'processed'
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def search(
        self,
        query_embedding: list[float],
        *,
        organization_id: UUID,
        top_k: int,
        min_similarity: float | None = None,
        document_id: UUID | None = None,
    ) -> list[OrganizationPolicySearchRow]:
        if len(query_embedding) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} "
                f"does not match expected {EMBEDDING_DIMENSION}"
            )

        params: dict[str, Any] = {
            "query_embedding": query_embedding,
            "organization_id": str(organization_id),
            "top_k": top_k,
        }
        sql = self._QUERY
        if document_id is not None:
            sql += " AND c.document_id = :document_id"
            params["document_id"] = str(document_id)
        if min_similarity is not None:
            sql += " AND 1 - (c.embedding <=> :query_embedding) >= :min_similarity"
            params["min_similarity"] = min_similarity
        sql += """
            ORDER BY c.embedding <=> :query_embedding
            LIMIT :top_k
        """

        stmt = text(sql).bindparams(
            bindparam("query_embedding", type_=Vector(EMBEDDING_DIMENSION))
        )
        try:
            rows = self.session.execute(stmt, params).mappings().all()
        except SQLAlchemyError as exc:
            logger.error("Organization policy vector search failed: {}", exc)
            raise DatabaseError("Organization policy search failed") from exc

        return [
            OrganizationPolicySearchRow(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                document_name=row["document_name"],
                content=row["content"],
                section_title=row["section_title"],
                clause_reference=row["clause_reference"],
                similarity=float(row["similarity"]),
                metadata=row["metadata"] or {},
                document_type=row.get("document_type"),
                document_version=row.get("document_version"),
            )
            for row in rows
        ]
