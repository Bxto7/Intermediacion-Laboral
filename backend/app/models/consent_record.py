# RF: RNF001-RNF006 — Registro auditable de consentimientos (Ley N° 29733)
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ConsentRecord(Base):
    """Registro inmutable de consentimientos informados.

    Por Ley N° 29733 (Perú), cada recolección de datos personales debe
    ir acompañada de un registro del consentimiento, incluyendo el propósito,
    la IP del usuario y la versión de la política de privacidad aceptada.
    Estos registros NO se eliminan — son parte del audit trail legal.
    """

    __tablename__ = "consent_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    data_purpose = Column(
        String(100),
        nullable=False,
        comment="perfil | datos_economicos | portfolio | marketing",
    )
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    consent_given = Column(Boolean, nullable=False)
    consent_version = Column(String(20), default="1.0", nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
