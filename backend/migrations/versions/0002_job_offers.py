"""Add job_offers, applications and search_logs tables

RF: M03 RF036-RF055, M07 RF111-RF115

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-05 00:00:00.000000
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── job_offers ─────────────────────────────────────────────
    op.create_table(
        "job_offers",
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_skills", postgresql.JSONB(), server_default=sa.text("'[]'"), nullable=True),
        sa.Column("preferred_skills", postgresql.JSONB(), server_default=sa.text("'[]'"), nullable=True),
        sa.Column("district", sa.String(50), nullable=True),
        sa.Column("modality", sa.String(20), nullable=False, server_default="presencial"),
        sa.Column("salary_min", sa.Numeric(10, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(10, 2), nullable=True),
        sa.Column("worker_type_target", sa.String(20), server_default="cualquiera", nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=True),  # managed by pgvector
        sa.Column("views_count", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("applications_count", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["employer_id"], ["employers.id"]),
        sa.CheckConstraint("modality IN ('presencial','remoto','hibrido')", name="ck_job_offers_modality"),
        sa.CheckConstraint(
            "worker_type_target IN ('primer_empleo','experiencia','oficio','cualquiera')",
            name="ck_job_offers_worker_type_target",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_offers_employer_id", "job_offers", ["employer_id"])
    op.create_index("ix_job_offers_is_active", "job_offers", ["is_active"])

    op.execute("""
        ALTER TABLE job_offers
        DROP COLUMN IF EXISTS embedding,
        ADD COLUMN embedding vector(384)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_job_offers_embedding
        ON job_offers USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # ── applications ───────────────────────────────────────────
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("worker_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("job_offer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(20), server_default="enviada", nullable=False),
        sa.Column("match_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("cover_note", sa.Text(), nullable=True),
        sa.Column("employer_notes", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"]),
        sa.ForeignKeyConstraint(["job_offer_id"], ["job_offers.id"]),
        sa.CheckConstraint(
            "status IN ('enviada','en_revision','entrevista','descartada','contratada')",
            name="ck_applications_status",
        ),
        sa.UniqueConstraint("worker_id", "job_offer_id", name="uq_application_worker_job"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_applications_worker_id", "applications", ["worker_id"])
    op.create_index("ix_applications_job_offer_id", "applications", ["job_offer_id"])

    # ── search_logs ────────────────────────────────────────────
    op.create_table(
        "search_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("searcher_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("query_text", sa.Text(), nullable=True),
        sa.Column("query_embedding", sa.Text(), nullable=True),
        sa.Column("results_count", sa.Integer(), nullable=True),
        sa.Column("worker_type_filter", sa.String(20), nullable=True),
        sa.Column("district_filter", sa.String(50), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["searcher_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("""
        ALTER TABLE search_logs
        DROP COLUMN IF EXISTS query_embedding,
        ADD COLUMN query_embedding vector(384)
    """)


def downgrade() -> None:
    op.drop_table("search_logs")
    op.drop_table("applications")
    op.drop_index("ix_job_offers_embedding", "job_offers")
    op.drop_index("ix_job_offers_is_active", "job_offers")
    op.drop_index("ix_job_offers_employer_id", "job_offers")
    op.drop_table("job_offers")
