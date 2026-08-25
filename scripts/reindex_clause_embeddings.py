"""Regenerate clause embeddings from stored text using the configured model.

Use when embeddings were created with test/deterministic vectors or after
changing the embedding provider/model. Does not modify clause text or metadata.

Example:
    python scripts/reindex_clause_embeddings.py
    python scripts/reindex_clause_embeddings.py --version-id <uuid>
    python scripts/reindex_clause_embeddings.py --dry-run
"""

from __future__ import annotations

import argparse
from uuid import UUID

import app.models  # noqa: F401
from loguru import logger
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.ingestion.embedding_service import EmbeddingService
from app.models.clause import Clause


def _fetch_clauses(session: Session, version_id: UUID | None) -> list[Clause]:
    stmt = select(Clause).where(Clause.text.is_not(None))
    if version_id is not None:
        stmt = stmt.where(Clause.version_id == version_id)
    stmt = stmt.order_by(Clause.created_at)
    return list(session.scalars(stmt).all())


def reindex_embeddings(
    session: Session,
    *,
    version_id: UUID | None = None,
    batch_size: int | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Re-embed clauses from their stored text."""
    settings = get_settings()
    effective_batch = batch_size or settings.embedding_batch_size
    embedder = EmbeddingService()

    clauses = _fetch_clauses(session, version_id)
    if not clauses:
        logger.warning("No clauses found to reindex")
        return {"clauses": 0, "updated": 0}

    logger.info("Reindexing embeddings for {} clause(s)", len(clauses))
    if dry_run:
        sample = clauses[0]
        logger.info("Dry run — would embed clause {}: {!r}", sample.id, sample.text[:80])
        return {"clauses": len(clauses), "updated": 0}

    updated = 0
    for start in range(0, len(clauses), effective_batch):
        batch = clauses[start : start + effective_batch]
        texts = [clause.text for clause in batch]
        vectors = embedder.embed_texts(texts)
        if len(vectors) != len(batch):
            raise RuntimeError("Embedding count mismatch during reindex")

        for clause, vector in zip(batch, vectors, strict=True):
            clause.embedding = vector
            updated += 1

        session.flush()
        logger.info("Updated embeddings {}/{}", updated, len(clauses))

    session.commit()
    logger.info("Reindex complete — {} embedding(s) updated", updated)
    return {"clauses": len(clauses), "updated": updated}


def _verify_dimensions(session: Session) -> None:
    rows = session.execute(
        text(
            """
            SELECT vector_dims(embedding) AS dim, COUNT(*) AS cnt
            FROM clauses
            WHERE embedding IS NOT NULL
            GROUP BY vector_dims(embedding)
            ORDER BY dim
            """
        )
    ).mappings().all()
    for row in rows:
        logger.info("Stored embedding dimension {} — {} row(s)", row["dim"], row["cnt"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate clause embeddings from stored text")
    parser.add_argument(
        "--version-id",
        type=UUID,
        default=None,
        help="Limit reindex to a single regulation version",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Embedding batch size (defaults to REGTECH_EMBEDDING_BATCH_SIZE)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report how many clauses would be updated without writing",
    )
    args = parser.parse_args()

    engine = create_engine(get_settings().database_url)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        _verify_dimensions(session)
        stats = reindex_embeddings(
            session,
            version_id=args.version_id,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )
    print(stats)


if __name__ == "__main__":
    main()
