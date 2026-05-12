# RF: RF136-RF145 — Economic survey data for KPI: Reduccion Brecha Salarial
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class EconomicSurvey(Base):
    __tablename__ = "economic_surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
    )
    survey_phase = Column(String(10), nullable=False)
    monthly_income = Column(LargeBinary, nullable=False)
    employment_type = Column(String(30), nullable=True)
    consent_given = Column(Boolean, default=False, nullable=False)
    surveyed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
