"""Add pgvector embedding column and clause enrichment fields.

Revision ID: 002_pgvector
Revises: 001_initial
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_pgvector"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSION = 1024


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("clauses", sa.Column("section", sa.String(length=500), nullable=True))
    op.add_column("clauses", sa.Column("page_number", sa.Integer(), nullable=True))
    op.add_column("clauses", sa.Column("page_end", sa.Integer(), nullable=True))
    op.add_column(
        "regulation_versions",
        sa.Column("storage_path", sa.String(length=1000), nullable=True),
    )

    op.execute(
        f"ALTER TABLE clauses ADD COLUMN embedding vector({EMBEDDING_DIMENSION})"
    )

    op.drop_index("ix_clauses_version_clause", table_name="clauses")
    op.create_index(
        "ix_clauses_version_clause_unique",
        "clauses",
        ["version_id", "clause_number"],
        unique=True,
    )
    op.create_index(
        "uq_regulation_versions_content_hash",
        "regulation_versions",
        ["content_hash"],
        unique=True,
    )
    op.execute(
        "CREATE INDEX ix_clauses_embedding_hnsw ON clauses "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_clauses_embedding_hnsw")
    op.drop_index("uq_regulation_versions_content_hash", table_name="regulation_versions")
    op.drop_index("ix_clauses_version_clause_unique", table_name="clauses")
    op.create_index("ix_clauses_version_clause", "clauses", ["version_id", "clause_number"])
    op.drop_column("clauses", "embedding")
    op.drop_column("regulation_versions", "storage_path")
    op.drop_column("clauses", "page_end")
    op.drop_column("clauses", "page_number")
    op.drop_column("clauses", "section")
