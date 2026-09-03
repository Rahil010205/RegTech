"""Add organization policy document and chunk tables with pgvector.

Revision ID: 003_org_policy
Revises: 002_pgvector
Create Date: 2026-08-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.models.clause import EMBEDDING_DIMENSION

revision: str = "003_org_policy"
down_revision: Union[str, None] = "002_pgvector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "organization_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("document_name", sa.String(length=500), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=True),
        sa.Column("source_filename", sa.String(length=500), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_organization_documents_organization_id",
        "organization_documents",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_documents_org_status",
        "organization_documents",
        ["organization_id", "status"],
    )

    op.create_table(
        "organization_policy_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organization_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("section_title", sa.Text(), nullable=True),
        sa.Column("clause_reference", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute(
        f"ALTER TABLE organization_policy_chunks "
        f"ADD COLUMN embedding vector({EMBEDDING_DIMENSION}) NOT NULL"
    )
    op.create_index(
        "ix_organization_policy_chunks_document_id",
        "organization_policy_chunks",
        ["document_id"],
    )
    op.create_index(
        "ix_organization_policy_chunks_organization_id",
        "organization_policy_chunks",
        ["organization_id"],
    )
    op.create_index(
        "uq_org_policy_chunks_document_index",
        "organization_policy_chunks",
        ["document_id", "chunk_index"],
        unique=True,
    )
    op.execute(
        "CREATE INDEX ix_org_policy_chunks_embedding_hnsw "
        "ON organization_policy_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_org_policy_chunks_embedding_hnsw")
    op.drop_index("uq_org_policy_chunks_document_index", table_name="organization_policy_chunks")
    op.drop_index(
        "ix_organization_policy_chunks_organization_id",
        table_name="organization_policy_chunks",
    )
    op.drop_index(
        "ix_organization_policy_chunks_document_id",
        table_name="organization_policy_chunks",
    )
    op.drop_table("organization_policy_chunks")
    op.drop_index("ix_organization_documents_org_status", table_name="organization_documents")
    op.drop_index("ix_organization_documents_organization_id", table_name="organization_documents")
    op.drop_table("organization_documents")
