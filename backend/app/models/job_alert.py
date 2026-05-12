# RF: RF111-RF117 (M07)
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class JobAlert(Base):
    __tablename__ = "job_alerts"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")
    )
    worker_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), nullable=False, index=True)
    worker_type: Mapped[str] = mapped_column(String(20), nullable=False)
    keywords: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'"))
    districts: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'"))
    trade_categories: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'"))
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
