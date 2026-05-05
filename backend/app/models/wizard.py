# RF: RF096-RF105
from datetime import datetime

from sqlalchemy import Integer, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WizardProgress(Base):
    __tablename__ = "wizard_progress"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    worker_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), nullable=False, unique=True
    )
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    answers: Mapped[dict] = mapped_column(JSONB, default=dict)
    extracted_skills: Mapped[list] = mapped_column(JSONB, default=list)
    job_interests: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'"))
    last_saved_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
