"""Add ML matching tables for Sprint 3

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-06 01:00:00.000000
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("version_tag", sa.String(50), nullable=False, unique=True),
        sa.Column("worker_type", sa.String(20), nullable=True),
        sa.Column("algorithm", sa.String(100), nullable=False),
        sa.Column("f1_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("precision_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("recall_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("feature_names", postgresql.JSONB, server_default=sa.text("'[]'")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("false")),
        sa.Column(
            "trained_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("deployed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_table(
        "equity_audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("worker_type", sa.String(20), nullable=False),
        sa.Column("gender", sa.String(10), nullable=True),
        sa.Column("district", sa.String(50), nullable=True),
        sa.Column("disparate_impact", sa.Numeric(5, 4), nullable=True),
        sa.Column("reranking_applied", sa.Boolean, server_default=sa.text("false")),
        sa.Column("original_rank", sa.Integer, nullable=True),
        sa.Column("adjusted_rank", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_table(
        "economic_surveys",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("survey_phase", sa.String(10), nullable=False),
        sa.Column("monthly_income", sa.LargeBinary, nullable=False),
        sa.Column("employment_type", sa.String(30), nullable=True),
        sa.Column(
            "consent_given",
            sa.Boolean,
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "surveyed_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("economic_surveys")
    op.drop_table("equity_audit_logs")
    op.drop_table("model_versions")
