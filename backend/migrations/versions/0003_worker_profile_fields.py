"""Add profile fields to workers and job_interests to wizard_progress

RF: M02 RF016-RF035, M06 RF096-RF105

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-05 01:00:00.000000
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Workers: add bio, job_title, username, education_level
    op.add_column("workers", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("workers", sa.Column("job_title", sa.String(100), nullable=True))
    op.add_column("workers", sa.Column("username", sa.String(50), nullable=True))
    op.add_column("workers", sa.Column("education_level", sa.String(50), nullable=True))
    op.create_unique_constraint("uq_workers_username", "workers", ["username"])

    # WizardProgress: add job_interests
    from sqlalchemy.dialects import postgresql
    op.add_column(
        "wizard_progress",
        sa.Column(
            "job_interests",
            postgresql.JSONB(),
            server_default=sa.text("'[]'"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("wizard_progress", "job_interests")
    op.drop_constraint("uq_workers_username", "workers", type_="unique")
    op.drop_column("workers", "education_level")
    op.drop_column("workers", "username")
    op.drop_column("workers", "job_title")
    op.drop_column("workers", "bio")
