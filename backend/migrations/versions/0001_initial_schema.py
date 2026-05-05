"""Initial schema — all tables, pgvector extension and HNSW indexes

RF: M01 RF001-RF015, M02 RF016-RF035, M03 RF036-RF055,
    M04 RF056-RF075, M05 RF076-RF095, M06 RF096-RF110,
    M07 RF118-RF125, M09 RF136-RF145, RNF001, RNF006, RNF011

Revision ID: 0001
Revises:
Create Date: 2026-05-04 00:00:00.000000
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ──────────────────────────────────────────────────────────────
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
# ──────────────────────────────────────────────────────────────


def upgrade() -> None:
    # ── 0. pgvector extension ──────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── 1. users ──────────────────────────────────────────────
    # RF001-RF015  M01 Identidad y Autenticación
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="worker"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # ── 2. workers ────────────────────────────────────────────
    # RF016-RF025  M02 Perfil del Trabajador
    op.create_table(
        "workers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "worker_type",
            sa.String(20),
            nullable=False,
            comment="primer_empleo | experiencia | oficio",
        ),
        sa.Column("full_name", postgresql.BYTEA(), nullable=False, comment="AES-256"),
        sa.Column("dni", postgresql.BYTEA(), nullable=False, comment="AES-256"),
        sa.Column("phone", postgresql.BYTEA(), nullable=True, comment="AES-256"),
        sa.Column("district", sa.String(50), nullable=True),
        sa.Column("trade_category", sa.String(50), nullable=True, comment="solo OFICIO"),
        sa.Column("years_experience", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "avg_rating",
            sa.Numeric(3, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "profile_completeness", sa.Integer(), nullable=False, server_default="0"
        ),
        # pgvector column — must be declared as text so Alembic serialises it correctly
        sa.Column(
            "embedding",
            sa.Text().with_variant(sa.Text(), "postgresql"),
            nullable=True,
            comment="vector(384) — HNSW index created separately",
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "worker_type IN ('primer_empleo','experiencia','oficio')",
            name="ck_workers_worker_type",
        ),
    )

    # Replace the placeholder text column with the native vector(384) type
    op.execute("ALTER TABLE workers DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE workers ADD COLUMN embedding vector(384)")

    # ── 3. employers ─────────────────────────────────────────
    # RF036-RF040  M03 Empleadores y Ofertas
    op.create_table(
        "employers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("ruc", postgresql.BYTEA(), nullable=False, comment="AES-256, 11 digits"),
        sa.Column("contact_name", postgresql.BYTEA(), nullable=False, comment="AES-256"),
        sa.Column("phone", postgresql.BYTEA(), nullable=True, comment="AES-256"),
        sa.Column("district", sa.String(50), nullable=True),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column(
            "is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # ── 4. portfolio_entries ──────────────────────────────────
    # RF056-RF065  M04 NLP de Competencias — portfolio visual (OFICIO)
    op.create_table(
        "portfolio_entries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("worker_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "extracted_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "photos",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("client_rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"], ondelete="CASCADE"),
    )
    op.execute(
        "ALTER TABLE portfolio_entries ADD COLUMN IF NOT EXISTS embedding vector(384)"
    )

    # ── 5. service_listings ───────────────────────────────────
    # RF118-RF125  M07 Marketplace de servicios (OFICIO)
    op.create_table(
        "service_listings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("worker_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("trade_category", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "enriched_keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "districts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("price_reference", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_unit", sa.String(20), nullable=True),
        sa.Column("availability", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("views_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"], ondelete="CASCADE"),
    )
    op.execute(
        "ALTER TABLE service_listings ADD COLUMN IF NOT EXISTS embedding vector(384)"
    )

    # ── 6. wizard_progress ────────────────────────────────────
    # RF096-RF105  M06 Asistente Identidad Laboral (PRIMER_EMPLEO)
    op.create_table(
        "wizard_progress",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("worker_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "answers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "extracted_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "last_saved_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("worker_id", name="uq_wizard_progress_worker_id"),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"], ondelete="CASCADE"),
    )

    # ── 7. generated_cvs ──────────────────────────────────────
    # RF106-RF110  M06 CV generado (PRIMER_EMPLEO + OFICIO)
    op.create_table(
        "generated_cvs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("worker_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "cv_type",
            sa.String(20),
            nullable=False,
            comment="wizard_based | portfolio_based | parsed",
        ),
        sa.Column("template_used", sa.String(50), nullable=True),
        sa.Column("file_url", sa.Text(), nullable=True, comment="URL firmada GCS/S3"),
        sa.Column(
            "generated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"], ondelete="CASCADE"),
    )

    # ── 8. audit_logs ─────────────────────────────────────────
    # RNF001, RNF006  Inmutable por diseño — no DELETE en producción
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── 9. HNSW indexes (pgvector) ────────────────────────────
    # Obligatorios según CLAUDE.md — m=16, ef_construction=64
    # M05 RF076-RF090, M07 RF111-RF125
    op.execute(
        """
        CREATE INDEX ix_workers_embedding_hnsw
        ON workers
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )
    op.execute(
        """
        CREATE INDEX ix_portfolio_entries_embedding_hnsw
        ON portfolio_entries
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )
    op.execute(
        """
        CREATE INDEX ix_service_listings_embedding_hnsw
        ON service_listings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # ── 10. Supporting B-tree indexes ────────────────────────
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_workers_user_id", "workers", ["user_id"])
    op.create_index("ix_workers_worker_type", "workers", ["worker_type"])
    op.create_index("ix_workers_district", "workers", ["district"])
    op.create_index("ix_portfolio_entries_worker_id", "portfolio_entries", ["worker_id"])
    op.create_index("ix_service_listings_worker_id", "service_listings", ["worker_id"])
    op.create_index("ix_service_listings_is_active", "service_listings", ["is_active"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    # ── Remove B-tree indexes ─────────────────────────────────
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_service_listings_is_active", table_name="service_listings")
    op.drop_index("ix_service_listings_worker_id", table_name="service_listings")
    op.drop_index("ix_portfolio_entries_worker_id", table_name="portfolio_entries")
    op.drop_index("ix_workers_district", table_name="workers")
    op.drop_index("ix_workers_worker_type", table_name="workers")
    op.drop_index("ix_workers_user_id", table_name="workers")
    op.drop_index("ix_users_email", table_name="users")

    # ── Remove HNSW indexes ───────────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_service_listings_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_portfolio_entries_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_workers_embedding_hnsw")

    # ── Drop tables in dependency order ───────────────────────
    op.drop_table("audit_logs")
    op.drop_table("generated_cvs")
    op.drop_table("wizard_progress")
    op.drop_table("service_listings")
    op.drop_table("portfolio_entries")
    op.drop_table("employers")
    op.drop_table("workers")
    op.drop_table("users")

    # ── Drop pgvector extension ───────────────────────────────
    op.execute("DROP EXTENSION IF EXISTS vector")
