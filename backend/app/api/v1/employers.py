# RF: RF036-RF050
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, encrypt_field, require_role
from app.models.application import Application
from app.models.audit_log import AuditLog
from app.models.employer import Employer
from app.models.job_offer import JobOffer
from app.schemas.common import MessageResponse
from app.schemas.employer import (
    EmployerProfileCreate,
    EmployerProfileResponse,
    EmployerProfileUpdate,
)
from app.schemas.job_offer import (
    ApplicationResponse,
    JobOfferCreate,
    JobOfferResponse,
    JobOfferUpdate,
)
from app.tasks.embeddings import generate_job_embedding
from app.tasks.notifications import notify_worker_hired

router = APIRouter(prefix="/employers", tags=["Empleadores"])
logger = structlog.get_logger()

STATUS_FLOW = {
    "enviada": ["en_revision", "descartada"],
    "en_revision": ["entrevista", "descartada"],
    "entrevista": ["contratada", "descartada"],
    "contratada": [],
    "descartada": [],
}


def _build_offer_response(offer: JobOffer, employer_name: str) -> JobOfferResponse:
    days_until_expiry: int | None = None
    if offer.expires_at:
        delta = offer.expires_at - datetime.now(tz=UTC)
        days_until_expiry = max(0, delta.days)

    return JobOfferResponse(
        id=str(offer.id),
        employer_id=str(offer.employer_id),
        employer_name=employer_name,
        title=offer.title,
        description=offer.description,
        required_skills=offer.required_skills or [],
        preferred_skills=offer.preferred_skills or [],
        district=offer.district,
        modality=offer.modality,
        salary_min=offer.salary_min,
        salary_max=offer.salary_max,
        worker_type_target=offer.worker_type_target,
        is_active=offer.is_active,
        expires_at=offer.expires_at,
        views_count=offer.views_count or 0,
        applications_count=offer.applications_count or 0,
        days_until_expiry=days_until_expiry,
        created_at=offer.created_at,
    )


async def _get_employer_or_404(user_id: str, db: AsyncSession) -> Employer:
    result = await db.execute(select(Employer).where(Employer.user_id == user_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de empleador no encontrado")
    return emp


@router.post("/profile", response_model=EmployerProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_employer_profile(
    body: EmployerProfileCreate,
    payload: dict = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db),
) -> EmployerProfileResponse:
    existing = await db.execute(select(Employer).where(Employer.user_id == payload["sub"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya tienes un perfil de empleador")

    emp = Employer(
        user_id=payload["sub"],
        company_name=body.company_name,
        ruc=encrypt_field(body.ruc),
        contact_name=encrypt_field(body.contact_name),
        phone=encrypt_field(body.phone) if body.phone else None,
        district=body.district.value if body.district else None,
        sector=body.sector,
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)
    logger.info("employer_profile_created", employer_id=str(emp.id))
    return EmployerProfileResponse.model_validate(emp)


@router.get("/profile", response_model=EmployerProfileResponse)
async def get_employer_profile(
    payload: dict = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db),
) -> EmployerProfileResponse:
    emp = await _get_employer_or_404(payload["sub"], db)
    return EmployerProfileResponse.model_validate(emp)


@router.patch("/profile", response_model=EmployerProfileResponse)
async def update_employer_profile(
    body: EmployerProfileUpdate,
    payload: dict = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db),
) -> EmployerProfileResponse:
    emp = await _get_employer_or_404(payload["sub"], db)
    update_data = body.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "contact_name" and value is not None:
            emp.contact_name = encrypt_field(value)
        elif field == "phone":
            emp.phone = encrypt_field(value) if value else None
        elif field == "district" and value is not None:
            emp.district = value.value if hasattr(value, "value") else value
        else:
            setattr(emp, field, value)

    audit = AuditLog(
        user_id=payload["sub"],
        action="employer_profile_updated",
        entity_type="employer",
        entity_id=str(emp.id),
        details={"updated_fields": list(update_data.keys())},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(emp)
    return EmployerProfileResponse.model_validate(emp)


@router.post("/jobs", response_model=JobOfferResponse, status_code=status.HTTP_201_CREATED)
async def create_job_offer(
    body: JobOfferCreate,
    payload: dict = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db),
) -> JobOfferResponse:
    emp = await _get_employer_or_404(payload["sub"], db)

    modality = body.modality
    if modality == "híbrido":
        modality = "hibrido"

    offer = JobOffer(
        employer_id=str(emp.id),
        title=body.title,
        description=body.description,
        required_skills=body.required_skills,
        preferred_skills=body.preferred_skills,
        district=body.district.value if body.district else None,
        modality=modality,
        salary_min=body.salary_min,
        salary_max=body.salary_max,
        worker_type_target=body.worker_type_target if isinstance(body.worker_type_target, str) else body.worker_type_target.value,
        expires_at=body.expires_at,
        is_active=True,
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)

    generate_job_embedding.delay(str(offer.id))
    logger.info("job_offer_created", offer_id=str(offer.id), employer_id=str(emp.id))
    return _build_offer_response(offer, emp.company_name)


@router.get("/jobs", response_model=list[JobOfferResponse])
async def list_job_offers(
    limit: int = 20,
    offset: int = 0,
    payload: dict = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db),
) -> list[JobOfferResponse]:
    limit = min(limit, 100)
    emp = await _get_employer_or_404(payload["sub"], db)

    result = await db.execute(
        select(JobOffer)
        .where(JobOffer.employer_id == str(emp.id))
        .order_by(JobOffer.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    offers = result.scalars().all()
    return [_build_offer_response(o, emp.company_name) for o in offers]


@router.patch("/jobs/{job_id}", response_model=JobOfferResponse)
async def update_job_offer(
    job_id: str,
    body: JobOfferUpdate,
    payload: dict = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db),
) -> JobOfferResponse:
    emp = await _get_employer_or_404(payload["sub"], db)
    result = await db.execute(select(JobOffer).where(JobOffer.id == job_id))
    offer = result.scalar_one_or_none()

    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oferta no encontrada")
    if str(offer.employer_id) != str(emp.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes modificar esta oferta")

    update_data = body.model_dump(exclude_unset=True)
    re_embed = False

    for field, value in update_data.items():
        if field == "district" and value is not None:
            setattr(offer, field, value.value if hasattr(value, "value") else value)
        elif field == "worker_type_target" and value is not None:
            setattr(offer, field, value.value if hasattr(value, "value") else value)
        else:
            setattr(offer, field, value)
        if field in ("description", "required_skills"):
            re_embed = True

    if re_embed:
        generate_job_embedding.delay(str(offer.id))

    await db.commit()
    await db.refresh(offer)
    return _build_offer_response(offer, emp.company_name)


@router.delete("/jobs/{job_id}", response_model=MessageResponse)
async def deactivate_job_offer(
    job_id: str,
    payload: dict = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    emp = await _get_employer_or_404(payload["sub"], db)
    result = await db.execute(select(JobOffer).where(JobOffer.id == job_id))
    offer = result.scalar_one_or_none()

    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oferta no encontrada")
    if str(offer.employer_id) != str(emp.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes modificar esta oferta")

    offer.is_active = False
    offer.expires_at = datetime.now(tz=UTC)

    audit = AuditLog(
        user_id=payload["sub"],
        action="job_offer_deactivated",
        entity_type="job_offer",
        entity_id=str(offer.id),
    )
    db.add(audit)
    await db.commit()
    return MessageResponse(message="Oferta desactivada correctamente")


@router.get("/jobs/{job_id}/applications", response_model=list[ApplicationResponse])
async def list_job_applications(
    job_id: str,
    limit: int = 20,
    offset: int = 0,
    payload: dict = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationResponse]:
    limit = min(limit, 100)
    emp = await _get_employer_or_404(payload["sub"], db)

    offer_result = await db.execute(select(JobOffer).where(JobOffer.id == job_id))
    offer = offer_result.scalar_one_or_none()
    if not offer or str(offer.employer_id) != str(emp.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    result = await db.execute(
        select(Application)
        .where(Application.job_offer_id == job_id)
        .limit(limit)
        .offset(offset)
    )
    apps = result.scalars().all()

    return [
        ApplicationResponse(
            id=str(a.id),
            job_offer_id=str(a.job_offer_id),
            worker_id=str(a.worker_id),
            status=a.status,
            match_score=a.match_score,
            cover_note=a.cover_note,
            applied_at=a.applied_at,
            job_title=offer.title,
        )
        for a in apps
    ]


@router.patch("/jobs/{job_id}/applications/{app_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    job_id: str,
    app_id: str,
    body: dict,
    payload: dict = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    emp = await _get_employer_or_404(payload["sub"], db)

    offer_result = await db.execute(select(JobOffer).where(JobOffer.id == job_id))
    offer = offer_result.scalar_one_or_none()
    if not offer or str(offer.employer_id) != str(emp.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    app_result = await db.execute(
        select(Application).where(Application.id == app_id, Application.job_offer_id == job_id)
    )
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postulacion no encontrada")

    new_status = body.get("status", "")
    allowed = STATUS_FLOW.get(application.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede cambiar de '{application.status}' a '{new_status}'",
        )

    application.status = new_status
    application.updated_at = datetime.now(tz=UTC)

    if new_status == "contratada":
        notify_worker_hired.delay(str(application.worker_id), str(application.job_offer_id))

    await db.commit()
    await db.refresh(application)

    return ApplicationResponse(
        id=str(application.id),
        job_offer_id=str(application.job_offer_id),
        worker_id=str(application.worker_id),
        status=application.status,
        match_score=application.match_score,
        cover_note=application.cover_note,
        applied_at=application.applied_at,
        job_title=offer.title,
    )
