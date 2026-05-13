# RF: RF041-RF055 (M03) — Postulaciones a ofertas de empleo
from decimal import Decimal
import uuid as uuid_mod

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, require_role
from app.models.employer import Employer
from app.models.job import JobRequestApplication
from app.models.job_offer import JobOffer
from app.models.worker import Worker
from app.schemas.contract import ApplicationCreate, ApplicationResponse

router = APIRouter(prefix="/applications", tags=["Postulaciones"])
logger = structlog.get_logger()


def _build_app_response(app: JobRequestApplication, offer_title: str, employer_name: str) -> ApplicationResponse:
    return ApplicationResponse(
        id=str(app.id),
        job_offer_id=str(app.job_request_id),
        worker_id=str(app.worker_id),
        cover_message=app.message,
        proposed_rate=app.proposed_rate,
        status=app.status,
        created_at=app.created_at,
        offer_title=offer_title,
        employer_name=employer_name,
    )


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    body: ApplicationCreate,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """RF047 — Trabajador se postula a una oferta de empleo."""
    worker_res = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
    worker = worker_res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Perfil de trabajador no encontrado")

    offer_res = await db.execute(select(JobOffer).where(JobOffer.id == str(body.job_offer_id)))
    offer = offer_res.scalar_one_or_none()
    if not offer or not offer.is_active:
        raise HTTPException(status_code=404, detail="Oferta no encontrada o inactiva")

    existing = await db.execute(
        select(JobRequestApplication).where(
            JobRequestApplication.job_request_id == str(body.job_offer_id),
            JobRequestApplication.worker_id == str(worker.id),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe una postulación a esta oferta")

    application = JobRequestApplication(
        id=uuid_mod.uuid4(),
        job_request_id=str(body.job_offer_id),
        worker_id=str(worker.id),
        message=body.cover_message,
        proposed_rate=Decimal(str(body.proposed_rate)) if body.proposed_rate else None,
        status="PENDING",
    )
    db.add(application)

    offer.applications_count = (offer.applications_count or 0) + 1
    await db.commit()
    await db.refresh(application)

    emp_res = await db.execute(select(Employer).where(Employer.id == str(offer.employer_id)))
    employer = emp_res.scalar_one_or_none()

    logger.info("application_submitted", worker_id=str(worker.id), offer_id=str(offer.id))
    return _build_app_response(application, offer.title, employer.company_name if employer else "")


@router.get("/my", response_model=list[ApplicationResponse])
async def get_my_applications(
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationResponse]:
    """RF048 — Lista las postulaciones del trabajador autenticado."""
    worker_res = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
    worker = worker_res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    apps_res = await db.execute(
        select(JobRequestApplication)
        .where(JobRequestApplication.worker_id == str(worker.id))
        .order_by(JobRequestApplication.created_at.desc())
    )
    applications = apps_res.scalars().all()

    offer_ids = [a.job_request_id for a in applications]
    offer_map: dict[str, JobOffer] = {}
    emp_map: dict[str, str] = {}

    if offer_ids:
        offers_res = await db.execute(select(JobOffer).where(JobOffer.id.in_(offer_ids)))
        for o in offers_res.scalars().all():
            offer_map[str(o.id)] = o

        emp_ids = list({str(o.employer_id) for o in offer_map.values()})
        if emp_ids:
            emps_res = await db.execute(select(Employer).where(Employer.id.in_(emp_ids)))
            for e in emps_res.scalars().all():
                emp_map[str(e.id)] = e.company_name

    return [
        _build_app_response(
            a,
            offer_map[a.job_request_id].title if a.job_request_id in offer_map else "",
            emp_map.get(str(offer_map[a.job_request_id].employer_id), "") if a.job_request_id in offer_map else "",
        )
        for a in applications
    ]


@router.patch("/{application_id}/withdraw", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_application(
    application_id: str,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """RF049 — Retirar una postulación pendiente."""
    worker_res = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
    worker = worker_res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    app_res = await db.execute(
        select(JobRequestApplication).where(
            JobRequestApplication.id == application_id,
            JobRequestApplication.worker_id == str(worker.id),
        )
    )
    application = app_res.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if application.status != "PENDING":
        raise HTTPException(status_code=409, detail="Solo se pueden retirar postulaciones en estado PENDING")

    application.status = "WITHDRAWN"
    await db.commit()
    logger.info("application_withdrawn", application_id=application_id)
