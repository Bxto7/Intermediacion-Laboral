# RF: RF096-RF100
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, require_role
from app.models.worker import Worker
from app.schemas.wizard import STEP_HINTS, WizardStepRequest, WizardStepResponse
from app.services.cv_builder.wizard_service import (
    get_or_create_wizard,
    get_wizard_summary,
    save_wizard_step,
)

router = APIRouter(prefix="/wizard", tags=["Wizard"])
logger = structlog.get_logger()


async def _require_primer_empleo(payload: dict, db: AsyncSession) -> Worker:
    result = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de trabajador no encontrado")
    if worker.worker_type != "primer_empleo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El wizard es exclusivo para trabajadores de tipo 'primer_empleo'",
        )
    return worker


@router.get("/progress")
async def get_wizard_progress(
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    worker = await _require_primer_empleo(payload, db)
    wizard = await get_or_create_wizard(str(worker.id), db)

    return {
        "current_step": wizard.current_step,
        "is_complete": wizard.current_step >= 6,
        "answers": wizard.answers or {},
        "extracted_skills": wizard.extracted_skills or [],
        "job_interests": wizard.job_interests or [],
        "next_step_hint": STEP_HINTS.get(min(wizard.current_step + 1, 6), ""),
    }


@router.post("/step", response_model=WizardStepResponse)
async def submit_wizard_step(
    body: WizardStepRequest,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> WizardStepResponse:
    worker = await _require_primer_empleo(payload, db)
    wizard = await save_wizard_step(str(worker.id), body.step, body.data, db)

    if wizard.current_step >= 6:
        worker.profile_completeness = 80
        await db.commit()

    is_complete = wizard.current_step >= 6
    next_hint = STEP_HINTS.get(min(wizard.current_step + 1, 6), "Wizard completo") if not is_complete else "Tu CV esta listo para descargar"

    logger.info("wizard_step_saved", worker_id=str(worker.id), step=body.step, current=wizard.current_step)

    return WizardStepResponse(
        current_step=wizard.current_step,
        is_complete=is_complete,
        extracted_skills=wizard.extracted_skills or [],
        next_step_hint=next_hint,
    )


@router.get("/summary")
async def get_wizard_summary_endpoint(
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    worker = await _require_primer_empleo(payload, db)
    return await get_wizard_summary(str(worker.id), db)
