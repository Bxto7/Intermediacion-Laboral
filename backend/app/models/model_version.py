# RF: RF086-RF095 — Model versioning for the matching engine
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_tag = Column(String(50), nullable=False, unique=True)
    worker_type = Column(String(20), nullable=True)
    algorithm = Column(String(100), nullable=False)
    f1_score = Column(Numeric(5, 4), nullable=True)
    precision_score = Column(Numeric(5, 4), nullable=True)
    recall_score = Column(Numeric(5, 4), nullable=True)
    feature_names = Column(JSONB, default=list)
    is_active = Column(Boolean, default=False)
    trained_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
