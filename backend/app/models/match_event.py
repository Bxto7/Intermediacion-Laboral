# RF: RF076-RF095, M05 Motor ML de Emparejamiento — audit trail
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class MatchEvent(Base):
    """Audit table for every ML matching event.

    Records the inputs and outputs of the combined_score calculation so that:
    - Equity audits can detect disparate impact (RF146-RF150)
    - KPIs like Tasa Cold-Start Superado can be computed (see CLAUDE.md)
    - Explainability traces are available per recommendation (RF151-RF155)
    """

    __tablename__ = "match_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    worker_type = Column(String(20), nullable=False, index=True)
    matched_job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_offers.id", ondelete="SET NULL"),
        nullable=True,
    )
    matched_listing_id = Column(
        UUID(as_uuid=True),
        ForeignKey("service_listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    cosine_sim = Column(Numeric(5, 4), nullable=True)
    ml_score = Column(Numeric(5, 4), nullable=True)
    reputation_score = Column(Numeric(5, 4), nullable=True)
    combined_score = Column(Numeric(5, 4), nullable=True)
    rank_position = Column(Integer, nullable=True)
    action = Column(String(20), nullable=True)
    equity_flag = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
