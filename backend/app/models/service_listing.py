# RF: RF118-RF125
from datetime import datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ServiceListing(Base):
    __tablename__ = "service_listings"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    worker_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), nullable=False)
    trade_category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    enriched_keywords: Mapped[list] = mapped_column(JSONB, default=list)
    districts: Mapped[list] = mapped_column(JSONB, default=list)
    price_reference: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), onupdate=datetime.utcnow
    )
