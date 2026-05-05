import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.employer import Employer
    from app.models.job import JobRequest
    from app.models.worker import Worker


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_requests.id"), nullable=False)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False, index=True)
    employer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employers.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="CONFIRMED", index=True)
    agreed_rate: Mapped[float | None] = mapped_column(Numeric(8, 2))
    rate_type: Mapped[str | None] = mapped_column(String(10))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    final_amount: Mapped[float | None] = mapped_column(Numeric(8, 2))
    payment_method: Mapped[str | None] = mapped_column(String(30))
    payment_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    work_evidence: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    description_done: Mapped[str | None] = mapped_column(Text)
    cancelled_reason: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    job_request: Mapped["JobRequest"] = relationship("JobRequest", back_populates="contracts")
    worker: Mapped["Worker"] = relationship("Worker", back_populates="contracts")
    employer: Mapped["Employer"] = relationship("Employer", back_populates="contracts")
    ratings: Mapped[list["Rating"]] = relationship("Rating", back_populates="contract")


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("contract_id", "rater_id", name="uq_rating_contract_rater"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    rater_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rated_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rater_role: Mapped[str] = mapped_column(String(10), nullable=False)
    overall_score: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False)
    quality_score: Mapped[float | None] = mapped_column(Numeric(2, 1))
    punctuality_score: Mapped[float | None] = mapped_column(Numeric(2, 1))
    communication_score: Mapped[float | None] = mapped_column(Numeric(2, 1))
    fairness_score: Mapped[float | None] = mapped_column(Numeric(2, 1))
    comment: Mapped[str | None] = mapped_column(String(300))
    sentiment: Mapped[str | None] = mapped_column(String(10))
    is_reported: Mapped[bool] = mapped_column(Boolean, default=False)
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False)
    worker_response: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    contract: Mapped["Contract"] = relationship("Contract", back_populates="ratings")
