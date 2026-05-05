import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.job import JobRequest
    from app.models.user import User
    from app.models.worker import Worker


class RecommendationLog(Base):
    __tablename__ = "recommendation_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_requests.id"), nullable=False, index=True)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False, index=True)
    cosine_similarity: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    ml_score: Mapped[float | None] = mapped_column(Numeric(6, 4))
    reputation_score: Mapped[float | None] = mapped_column(Numeric(6, 4))
    combined_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    shap_top_features: Mapped[dict | None] = mapped_column(JSONB)
    rank_position: Mapped[int | None] = mapped_column(SmallInteger)
    was_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    resulted_in_contract: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    alpha_used: Mapped[float] = mapped_column(Numeric(3, 2), default=0.50)
    beta_used: Mapped[float] = mapped_column(Numeric(3, 2), default=0.30)
    gamma_used: Mapped[float] = mapped_column(Numeric(3, 2), default=0.20)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

    job_request: Mapped["JobRequest"] = relationship("JobRequest", back_populates="recommendation_logs")
    worker: Mapped["Worker"] = relationship("Worker", back_populates="recommendation_logs")


class SearchLog(Base):
    __tablename__ = "search_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("job_requests.id"), nullable=True)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False, index=True)
    appeared_in_results: Mapped[bool] = mapped_column(Boolean, default=True)
    rank_position: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

    job_request: Mapped[Optional["JobRequest"]] = relationship("JobRequest", back_populates="search_logs")
    worker: Mapped["Worker"] = relationship("Worker", back_populates="search_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    action_url: Mapped[str | None] = mapped_column(String(500))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notifications")


class EconomicSurvey(Base):
    __tablename__ = "economic_surveys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False, index=True)
    survey_type: Mapped[str] = mapped_column(String(10), nullable=False)
    monthly_income_before: Mapped[float | None] = mapped_column(Numeric(8, 2))
    monthly_income_after: Mapped[float | None] = mapped_column(Numeric(8, 2))
    formal_contracts_6m: Mapped[int | None] = mapped_column(SmallInteger)
    informal_contracts_6m: Mapped[int | None] = mapped_column(SmallInteger)
    days_to_first_job: Mapped[int | None] = mapped_column(SmallInteger)
    digital_barrier_device: Mapped[str | None] = mapped_column(String(30))
    digital_barrier_connectivity: Mapped[str | None] = mapped_column(String(20))
    sus_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    equity_perception: Mapped[int | None] = mapped_column(SmallInteger)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    worker: Mapped["Worker"] = relationship("Worker", back_populates="economic_surveys")


class AuditLog(Base):
    """Tabla append-only — nunca DELETE/UPDATE."""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    old_values: Mapped[dict | None] = mapped_column(JSONB)
    new_values: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")


class SystemConfig(Base):
    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
