# RF: RF111-RF115
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SearchLog(Base):
    __tablename__ = "search_logs"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")
    )
    searcher_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )
    query_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    query_embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    results_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    worker_type_filter: Mapped[str | None] = mapped_column(String(20), nullable=True)
    district_filter: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))
