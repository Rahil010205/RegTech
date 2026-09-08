"""Add document-level compliance assessment table.

Revision ID: 005_document_level_compliance
Revises: 004_risk_scoring
Create Date: 2026-09-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_document_level_compliance"
down_revision: Union[str, None] = "004_risk_scoring"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "compliance_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "policy_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organization_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "policy_clause_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organization_policy_chunks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "regulatory_clause_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clauses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("matching_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("compliance_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="NOT_DETERMINABLE"),
        sa.Column("explanation", sa.Text(), nullable=False, server_default=""),
        sa.Column("policy_evidence", sa.Text(), nullable=False, server_default=""),
        sa.Column("regulatory_requirement", sa.Text(), nullable=False, server_default=""),
        sa.Column("reasoning_summary", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("analysis_version", sa.String(length=50), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_compliance_assessments_organization_id",
        "compliance_assessments",
        ["organization_id"],
    )
    op.create_index(
        "ix_compliance_assessments_policy_document_id",
        "compliance_assessments",
        ["policy_document_id"],
    )
    op.create_index(
        "ix_compliance_assessments_policy_clause_id",
        "compliance_assessments",
        ["policy_clause_id"],
    )
    op.create_index(
        "ix_compliance_assessments_regulatory_clause_id",
        "compliance_assessments",
        ["regulatory_clause_id"],
    )
    op.create_unique_constraint(
        "uq_compliance_assessment_pair",
        "compliance_assessments",
        ["organization_id", "policy_document_id", "policy_clause_id", "regulatory_clause_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_compliance_assessment_pair", "compliance_assessments", type_="unique")
    op.drop_index("ix_compliance_assessments_regulatory_clause_id", table_name="compliance_assessments")
    op.drop_index("ix_compliance_assessments_policy_clause_id", table_name="compliance_assessments")
    op.drop_index("ix_compliance_assessments_policy_document_id", table_name="compliance_assessments")
    op.drop_index("ix_compliance_assessments_organization_id", table_name="compliance_assessments")
    op.drop_table("compliance_assessments")
