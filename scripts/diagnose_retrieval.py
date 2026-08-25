"""Diagnostic script for pgvector retrieval debugging."""

from __future__ import annotations

import app.models  # noqa: F401
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.ingestion.embedding_service import EmbeddingService


def main() -> None:
    query = "What are the requirements for customer data retention?"
    embedder = EmbeddingService()
    qvec = embedder.embed_query(query)
    print(f"Query dim: {len(qvec)}")
    print(f"Query head: {qvec[:5]}")

    engine = create_engine(get_settings().database_url)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT c.id, LEFT(c.text, 70) AS text_preview,
                       COALESCE(c.metadata->>'document_name', 'unknown') AS doc_name,
                       c.embedding <=> CAST(:qvec AS vector) AS cosine_distance,
                       1 - (c.embedding <=> CAST(:qvec AS vector)) AS similarity
                FROM clauses c
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> CAST(:qvec AS vector)
                LIMIT 10
                """
            ),
            {"qvec": str(qvec)},
        ).fetchall()

        print("\n=== Top 10 by cosine distance (real BGE query) ===")
        for row in rows:
            mapping = row._mapping
            print(
                f"dist={mapping['cosine_distance']:.4f} "
                f"sim={mapping['similarity']:.4f} | "
                f"{mapping['doc_name']} | {mapping['text_preview']}"
            )

        dupes = conn.execute(
            text(
                """
                SELECT
                    COALESCE(c.metadata->>'document_name', r.title) AS document_name,
                    c.clause_number,
                    LEFT(c.text, 80) AS text_preview,
                    COUNT(*) AS duplicate_count
                FROM clauses c
                INNER JOIN regulation_versions rv ON rv.id = c.version_id
                INNER JOIN regulations r ON r.id = rv.regulation_id
                GROUP BY 1, 2, 3
                HAVING COUNT(*) > 1
                ORDER BY duplicate_count DESC
                LIMIT 10
                """
            )
        ).fetchall()
        print("\n=== Duplicate clauses ===")
        for row in dupes:
            print(dict(row._mapping))


if __name__ == "__main__":
    main()
