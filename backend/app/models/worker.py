# RF: RF016-RF025
from datetime import datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), nullable=False)
    worker_type: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    dni: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    phone: Mapped[bytes | None] = mapped_column(BYTEA, nullable=True)
    district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    trade_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.00"))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    profile_completeness: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    username: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    education_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), onupdate=datetime.utcnow
    )
