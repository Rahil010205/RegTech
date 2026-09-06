"""Add clause criticality and compliance_risk_assessments table.

Revision ID: 004_risk_scoring
Revises: 003_org_policy
Create Date: 2026-09-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_risk_scoring"
down_revision: Union[str, None] = "003_org_policy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add criticality to clauses
    op.add_column(
        "clauses",
        sa.Column(
            "criticality",
            sa.String(length=20),
            nullable=True,
            server_default="MEDIUM",
        ),
    )

    # 2. Create compliance_risk_assessments table
    op.create_table(
        "compliance_risk_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "regulatory_clause_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clauses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "compliance_analysis_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("compliance_status", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "factor_breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "identified_gaps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("explanation", sa.Text(), nullable=False),
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
        "ix_compliance_risk_assessments_organization_id",
        "compliance_risk_assessments",
        ["organization_id"],
    )
    op.create_index(
        "ix_compliance_risk_assessments_regulatory_clause_id",
        "compliance_risk_assessments",
        ["regulatory_clause_id"],
    )
    op.create_index(
        "ix_compliance_risk_assessments_org_clause",
        "compliance_risk_assessments",
        ["organization_id", "regulatory_clause_id"],
    )
    op.create_index(
        "ix_compliance_risk_assessments_created_at",
        "compliance_risk_assessments",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_compliance_risk_assessments_created_at",
        table_name="compliance_risk_assessments",
    )
    op.drop_index(
        "ix_compliance_risk_assessments_org_clause",
        table_name="compliance_risk_assessments",
    )
    op.drop_index(
        "ix_compliance_risk_assessments_regulatory_clause_id",
        table_name="compliance_risk_assessments",
    )
    op.drop_index(
        "ix_compliance_risk_assessments_organization_id",
        table_name="compliance_risk_assessments",
    )
    op.drop_table("compliance_risk_assessments")
    op.drop_column("clauses", "criticality")
