import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.contract import Contract
    from app.models.employer import Employer
    from app.models.worker import Worker


class JobRequest(Base):
    __tablename__ = "job_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employers.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    office_required: Mapped[str] = mapped_column(String(100), nullable=False)
    zone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    required_date: Mapped[date | None] = mapped_column(Date)
    duration_days: Mapped[int | None] = mapped_column(SmallInteger)
    max_budget: Mapped[float | None] = mapped_column(Numeric(8, 2))
    status: Mapped[str] = mapped_column(String(20), default="PUBLISHED", index=True)
    sector: Mapped[str | None] = mapped_column(String(50))
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_config: Mapped[dict | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    employer: Mapped["Employer"] = relationship("Employer")
    applications: Mapped[list["JobRequestApplication"]] = relationship("JobRequestApplication", back_populates="job_request")
    contracts: Mapped[list["Contract"]] = relationship("Contract", back_populates="job_request")


class JobRequestApplication(Base):
    __tablename__ = "job_request_applications"
    __table_args__ = (UniqueConstraint("job_request_id", "worker_id", name="uq_application_job_worker"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_requests.id"), nullable=False, index=True)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False, index=True)
    message: Mapped[str | None] = mapped_column(Text)
    proposed_rate: Mapped[float | None] = mapped_column(Numeric(8, 2))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    job_request: Mapped["JobRequest"] = relationship("JobRequest", back_populates="applications")
    worker: Mapped["Worker"] = relationship("Worker")
