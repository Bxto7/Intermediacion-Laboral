# RF: RF036-RF055
from datetime import datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class JobOffer(Base):
    __tablename__ = "job_offers"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")
    )
    employer_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("employers.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'"))
    preferred_skills: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'"))
    district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    modality: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("modality IN ('presencial','remoto','hibrido')"),
        nullable=False,
        default="presencial",
    )
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    worker_type_target: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("worker_type_target IN ('primer_empleo','experiencia','oficio','cualquiera')"),
        default="cualquiera",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    applications_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))
