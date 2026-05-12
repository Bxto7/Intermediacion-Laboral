"""Add match_events audit table for ML matching engine

RF: M05 RF076-RF095, M10 RF146-RF155 (equity auditing)
KPIs: Tasa Cold-Start Superado, disparate impact ratio

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-06 00:00:00.000000
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "match_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("worker_type", sa.String(20), nullable=False),
        sa.Column(
            "matched_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_offers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "matched_listing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("service_listings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("cosine_sim", sa.Numeric(5, 4), nullable=True),
        sa.Column("ml_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("reputation_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("combined_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("rank_position", sa.Integer, nullable=True),
        sa.Column("action", sa.String(20), nullable=True),
        sa.Column(
            "equity_flag",
            sa.Boolean,
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_match_events_worker_id_created_at",
        "match_events",
        ["worker_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_match_events_worker_type_created_at",
        "match_events",
        ["worker_type", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_match_events_worker_type_created_at", "match_events")
    op.drop_index("ix_match_events_worker_id_created_at", "match_events")
    op.drop_table("match_events")
