# RF: RF106-RF110
from datetime import datetime

from sqlalchemy import String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GeneratedCV(Base):
    __tablename__ = "generated_cvs"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    worker_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), nullable=False)
    cv_type: Mapped[str] = mapped_column(String(20), nullable=False)
    template_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
