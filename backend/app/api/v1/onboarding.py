# RF: RF016-RF022
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, require_role
from app.models.worker import Worker
from app.schemas.common import WorkerType
from app.schemas.onboarding import OnboardingAnswers, OnboardingResponse, OnboardingStatus
from app.services.onboarding.detector import (
    create_worker_profile,
    detect_worker_type,
    get_next_step_url,
)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])
logger = structlog.get_logger()

ONBOARDING_MESSAGES = {
    "primer_empleo": "Bienvenido! Vamos a construir tu primer CV paso a paso.",
    "experiencia": "Bienvenido! Crea tu perfil profesional y conecta con empleadores.",
    "oficio": "Bienvenido! Muestra tu trabajo y encuentra nuevos clientes.",
}


@router.post("/detect-type", response_model=OnboardingResponse)
async def detect_type(
    body: OnboardingAnswers,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> OnboardingResponse:
    user_id = payload["sub"]

    existing_result = await db.execute(select(Worker).where(Worker.user_id == user_id))
    existing_worker = existing_result.scalar_one_or_none()

    worker_type = detect_worker_type(body)

    if existing_worker:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El perfil del trabajador ya existe. Usa la API de edicion de perfil para modificarlo.",
        )

    worker = await create_worker_profile(user_id, worker_type, body.trade_category, db)

    next_step = get_next_step_url(worker_type)

    logger.info("onboarding_completed", user_id=user_id, worker_type=worker_type.value)
    return OnboardingResponse(
        worker_type=worker_type,
        worker_id=worker.id,
        next_step=next_step,
        message=ONBOARDING_MESSAGES[worker_type.value],
    )



@router.get("/status", response_model=OnboardingStatus)
async def onboarding_status(
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> OnboardingStatus:
    user_id = payload["sub"]
    result = await db.execute(select(Worker).where(Worker.user_id == user_id))
    worker = result.scalar_one_or_none()

    if not worker:
        return OnboardingStatus(worker_type=None, profile_completeness=0, is_onboarded=False)

    return OnboardingStatus(
        worker_type=WorkerType(worker.worker_type),
        profile_completeness=worker.profile_completeness,
        is_onboarded=True,
    )
