# RF: RF043-RF055
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("worker_id", "job_offer_id", name="uq_application_worker_job"),
    )

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")
    )
    worker_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("workers.id"), nullable=False, index=True
    )
    job_offer_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("job_offers.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("status IN ('enviada','en_revision','entrevista','descartada','contratada')"),
        nullable=False,
        default="enviada",
    )
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    cover_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    employer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))
