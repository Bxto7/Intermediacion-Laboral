# RF: RF136-RF145 (M09), Ley N° 29733 — Encuesta económica (pre/post) con consentimiento
from datetime import UTC, datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, encrypt_field, require_role

logger = structlog.get_logger()
router = APIRouter(prefix="/surveys", tags=["surveys"])


class EconomicSurveyCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    worker_id: UUID
    survey_phase: str = Field(..., pattern="^(pre|post)$")
    monthly_income: float = Field(..., gt=0, lt=100_000)
    employment_type: str = Field(..., max_length=30)
    consent_given: bool


@router.post("/economic", status_code=201)
async def submit_economic_survey(
    body: EconomicSurveyCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_role(UserRole.WORKER)),
):
    """Registra encuesta económica pre/post inserción laboral.
    Requiere consentimiento explícito (Ley N° 29733).
    El ingreso mensual se cifra con AES-256 antes de persistir.
    """
    if not body.consent_given:
        raise HTTPException(
            status_code=400,
            detail="Se requiere consentimiento informado para registrar datos económicos (Ley N° 29733).",
        )

    from sqlalchemy import text

    worker_row = (
        await db.execute(
            text("SELECT id FROM workers WHERE id = :wid"),
            {"wid": str(body.worker_id)},
        )
    ).fetchone()
    if worker_row is None:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado.")

    existing = (
        await db.execute(
            text(
                "SELECT id FROM economic_surveys "
                "WHERE worker_id = :wid AND survey_phase = :phase"
            ),
            {"wid": str(body.worker_id), "phase": body.survey_phase},
        )
    ).fetchone()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe una encuesta '{body.survey_phase}' para este trabajador.",
        )

    encrypted_income = encrypt_field(str(body.monthly_income))

    await db.execute(
        text("""
            INSERT INTO economic_surveys
                (worker_id, survey_phase, monthly_income, employment_type, consent_given, surveyed_at)
            VALUES
                (:wid, :phase, :income, :etype, :consent, :now)
        """),
        {
            "wid": str(body.worker_id),
            "phase": body.survey_phase,
            "income": encrypted_income,
            "etype": body.employment_type,
            "consent": body.consent_given,
            "now": datetime.now(UTC),
        },
    )
    await db.commit()

    logger.info(
        "economic_survey_submitted",
        worker_id=str(body.worker_id),
        phase=body.survey_phase,
    )
    return {"status": "ok", "phase": body.survey_phase}
