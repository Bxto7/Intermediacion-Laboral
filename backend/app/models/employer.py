# RF: RF036-RF040
from datetime import datetime

from sqlalchemy import Boolean, String, text
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Employer(Base):
    __tablename__ = "employers"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ruc: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    contact_name: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    phone: Mapped[bytes | None] = mapped_column(BYTEA, nullable=True)
    district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
