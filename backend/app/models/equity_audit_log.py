# RF: RF146-RF155 — Equity audit trail for disparate impact monitoring
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class EquityAuditLog(Base):
    __tablename__ = "equity_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
    )
    worker_type = Column(String(20), nullable=False)
    gender = Column(String(10), nullable=True)
    district = Column(String(50), nullable=True)
    disparate_impact = Column(Numeric(5, 4), nullable=True)
    reranking_applied = Column(Boolean, default=False)
    original_rank = Column(Integer, nullable=True)
    adjusted_rank = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
