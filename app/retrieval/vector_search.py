"""PostgreSQL pgvector similarity search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy import bindparam, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import DatabaseError
from app.models.clause import EMBEDDING_DIMENSION
from app.retrieval.schemas import RetrievalFilters
from pgvector.sqlalchemy import Vector


@dataclass(frozen=True)
class VectorSearchRow:
    """Internal row returned from pgvector search."""

    clause_id: UUID
    document_id: UUID
    document_name: str | None
    regulator: str | None
    clause_number: str | None
    section: str | None
    text: str
    page_number: int | None
    metadata: dict[str, Any]
    similarity: float


class VectorSearchService:
    """Execute semantic search against clause embeddings stored in PostgreSQL.

    Similarity metric
    -----------------
    Clause and query embeddings are L2-normalized during ingestion/querying.
    pgvector's cosine distance operator ``<=>`` returns:

        cosine_distance = 1 - cosine_similarity

    We convert that to a human-readable score with:

        similarity = 1 - (embedding <=> query_embedding)

    Result range:
        1.0 = identical direction (highly similar)
        0.0 = orthogonal / unrelated
    """

    _BASE_QUERY = """
        SELECT
            c.id AS clause_id,
            c.version_id AS document_id,
            COALESCE(c.metadata->>'document_name', r.title) AS document_name,
            COALESCE(c.metadata->>'regulator', r.regulator_code) AS regulator,
            c.clause_number,
            c.section,
            c.text,
            c.page_number,
            c.metadata,
            1 - (c.embedding <=> :query_embedding) AS similarity
        FROM clauses c
        INNER JOIN regulation_versions rv ON rv.id = c.version_id
        INNER JOIN regulations r ON r.id = rv.regulation_id
        INNER JOIN regulators reg ON reg.code = r.regulator_code
        WHERE c.embedding IS NOT NULL
          AND rv.status = 'completed'
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def search(
        self,
        query_embedding: list[float],
        *,
        top_k: int,
        filters: RetrievalFilters | None = None,
        min_similarity: float | None = None,
    ) -> list[VectorSearchRow]:
        """Search clause embeddings and return ranked results."""
        if len(query_embedding) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} "
                f"does not match expected {EMBEDDING_DIMENSION}"
            )

        where_clauses: list[str] = []
        params: dict[str, Any] = {
            "query_embedding": query_embedding,
            "top_k": top_k,
        }

        if filters:
            if filters.regulator:
                where_clauses.append(
                    "(r.regulator_code = :regulator OR c.metadata->>'regulator' = :regulator)"
                )
                params["regulator"] = filters.regulator
            if filters.jurisdiction:
                where_clauses.append(
                    "(reg.jurisdiction = :jurisdiction OR c.metadata->>'jurisdiction' = :jurisdiction)"
                )
                params["jurisdiction"] = filters.jurisdiction
            if filters.document_id:
                where_clauses.append("c.version_id = :document_id")
                params["document_id"] = str(filters.document_id)
            if filters.document_type:
                where_clauses.append(
                    "(r.document_type = :document_type OR c.metadata->>'document_type' = :document_type)"
                )
                params["document_type"] = filters.document_type
            if filters.section:
                where_clauses.append("c.section ILIKE :section")
                params["section"] = f"%{filters.section}%"
            if filters.effective_date:
                where_clauses.append("rv.effective_date = :effective_date")
                params["effective_date"] = filters.effective_date
            if filters.clause_number:
                where_clauses.append("c.clause_number = :clause_number")
                params["clause_number"] = filters.clause_number

        if min_similarity is not None:
            where_clauses.append("1 - (c.embedding <=> :query_embedding) >= :min_similarity")
            params["min_similarity"] = min_similarity

        query_sql = self._BASE_QUERY
        if where_clauses:
            query_sql += " AND " + " AND ".join(where_clauses)

        query_sql += """
            ORDER BY c.embedding <=> :query_embedding
            LIMIT :top_k
        """

        stmt = text(query_sql).bindparams(
            bindparam("query_embedding", type_=Vector(EMBEDDING_DIMENSION))
        )

        logger.debug(
            "Executing pgvector search — top_k={} filters={} min_similarity={}",
            top_k,
            filters.model_dump(exclude_none=True) if filters else {},
            min_similarity,
        )

        try:
            rows = self.session.execute(stmt, params).mappings().all()
        except SQLAlchemyError as exc:
            logger.error("pgvector search failed: {}", exc)
            raise DatabaseError(f"Vector search failed: {exc}") from exc

        results = [
            VectorSearchRow(
                clause_id=row["clause_id"],
                document_id=row["document_id"],
                document_name=row["document_name"],
                regulator=row["regulator"],
                clause_number=row["clause_number"],
                section=row["section"],
                text=row["text"],
                page_number=row["page_number"],
                metadata=row["metadata"] or {},
                similarity=float(row["similarity"]),
            )
            for row in rows
        ]

        logger.info("pgvector search returned {} clause(s)", len(results))
        return results
