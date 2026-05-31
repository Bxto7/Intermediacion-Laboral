# RF: RF026-RF031
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, decrypt_field, encrypt_field, require_role
from app.models.audit_log import AuditLog
from app.models.worker import Worker
from app.schemas.common import District, TradeCategory, WorkerType
from app.schemas.worker import CompletenessResponse, WorkerProfileResponse, WorkerProfileUpdate

router = APIRouter(prefix="/workers", tags=["Trabajadores"])
logger = structlog.get_logger()


async def _get_worker_or_404(user_id: str, db: AsyncSession) -> Worker:
    result = await db.execute(select(Worker).where(Worker.user_id == user_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")
    return worker


def _build_response(worker: Worker) -> WorkerProfileResponse:
    full_name = decrypt_field(worker.full_name) if worker.full_name else ""
    if full_name == "pendiente":
        full_name = ""

    district = None
    if worker.district:
        try:
            district = District(worker.district)
        except ValueError:
            district = None

    trade_category = None
    if worker.trade_category:
        try:
            trade_category = TradeCategory(worker.trade_category)
        except ValueError:
            trade_category = None

    return WorkerProfileResponse(
        id=worker.id,
        worker_type=WorkerType(worker.worker_type),
        full_name=full_name,
        display_name=full_name or (worker.username or "Trabajador"),
        district=district,
        trade_category=trade_category,
        years_experience=worker.years_experience or 0,
        avg_rating=float(worker.avg_rating or 0.0),
        is_available=worker.is_available,
        profile_completeness=worker.profile_completeness or 0,
        username=worker.username,
        slug=worker.username,
        bio=worker.bio,
        job_title=worker.job_title,
        created_at=worker.created_at,
    )


def _calculate_completeness(
    worker: Worker,
    wizard_step: int = 0,
    has_cv: bool = False,
    has_portfolio: bool = False,
) -> tuple[int, list[str], str]:
    wtype = WorkerType(worker.worker_type)
    percentage = 0
    missing: list[str] = []

    if wtype == WorkerType.PRIMER_EMPLEO:
        if worker.district:
            percentage += 20
        else:
            missing.append("Agrega tu distrito de residencia")
        if wizard_step >= 6:
            percentage += 40
        else:
            missing.append("Completa el wizard de 6 pasos")
        if has_cv:
            percentage += 40
        else:
            missing.append("Genera tu CV")
        next_action = (
            "Completa el wizard para generar tu CV" if wizard_step < 6 else "Descarga tu CV"
        )

    elif wtype == WorkerType.EXPERIENCIA:
        if worker.district:
            percentage += 20
        else:
            missing.append("Agrega tu distrito de residencia")
        if worker.years_experience and worker.years_experience > 0:
            percentage += 20
        else:
            missing.append("Indica tus anos de experiencia")
        next_action = "Agrega tu experiencia laboral"

    else:  # OFICIO
        if worker.district:
            percentage += 20
        else:
            missing.append("Agrega tu distrito de residencia")
        if worker.trade_category:
            percentage += 20
        else:
            missing.append("Selecciona tu categoria de oficio")
        if has_portfolio:
            percentage += 30
        else:
            missing.append("Agrega trabajos a tu portfolio")
        if worker.is_available:
            percentage += 30
        next_action = "Agrega trabajos a tu portfolio"

    return percentage, missing, next_action if missing else "Perfil completo!"


@router.get("/me", response_model=WorkerProfileResponse)
async def get_my_profile(
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> WorkerProfileResponse:
    worker = await _get_worker_or_404(payload["sub"], db)
    return _build_response(worker)


@router.patch("/me", response_model=WorkerProfileResponse)
async def update_my_profile(
    body: WorkerProfileUpdate,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> WorkerProfileResponse:
    worker = await _get_worker_or_404(payload["sub"], db)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "full_name" and value is not None:
            worker.full_name = encrypt_field(value)
        elif field == "phone":
            worker.phone = encrypt_field(value) if value else None
        elif field == "district" and value is not None:
            worker.district = value.value if hasattr(value, "value") else value
        elif field == "trade_category":
            worker.trade_category = (
                value.value if value and hasattr(value, "value") else value
            )
        else:
            setattr(worker, field, value)

    percentage, _, _ = _calculate_completeness(worker)
    worker.profile_completeness = percentage

    audit = AuditLog(
        user_id=payload["sub"],
        action="worker_profile_updated",
        entity_type="worker",
        entity_id=worker.id,
        details={"updated_fields": list(update_data.keys())},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(worker)

    logger.info("worker_profile_updated", worker_id=worker.id, fields=list(update_data.keys()))
    return _build_response(worker)


@router.get("/me/completeness", response_model=CompletenessResponse)
async def get_completeness(
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> CompletenessResponse:
    worker = await _get_worker_or_404(payload["sub"], db)
    percentage, missing, next_action = _calculate_completeness(worker)
    return CompletenessResponse(
        percentage=percentage,
        missing_fields=missing,
        next_action=next_action,
    )


@router.post("/apply", status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    body: dict,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.models.application import Application
    from app.models.employer import Employer
    from app.models.job_offer import JobOffer
    from app.models.search_log import SearchLog
    from app.tasks.notifications import notify_employer_new_application

    worker = await _get_worker_or_404(payload["sub"], db)

    if (worker.profile_completeness or 0) < 40:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completa tu perfil antes de postular (minimo 40% de completitud)",
        )

    job_offer_id = body.get("job_offer_id", "")
    cover_note = body.get("cover_note")

    offer_result = await db.execute(select(JobOffer).where(JobOffer.id == job_offer_id))
    offer = offer_result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oferta no encontrada")
    if not offer.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La oferta no esta activa")

    existing = await db.execute(
        select(Application).where(
            Application.worker_id == str(worker.id),
            Application.job_offer_id == job_offer_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya postulaste a esta oferta")

    application = Application(
        worker_id=str(worker.id),
        job_offer_id=job_offer_id,
        status="enviada",
        cover_note=cover_note,
    )
    db.add(application)

    offer.applications_count = (offer.applications_count or 0) + 1

    log = SearchLog(
        searcher_id=payload["sub"],
        query_text=f"apply:{job_offer_id}",
        results_count=1,
    )
    db.add(log)

    await db.commit()
    await db.refresh(application)

    emp_result = await db.execute(select(Employer).where(Employer.id == str(offer.employer_id)))
    emp = emp_result.scalar_one_or_none()
    notify_employer_new_application.delay(
        str(emp.id) if emp else "",
        str(application.job_offer_id),
        str(worker.id),
    )

    return {
        "id": str(application.id),
        "job_offer_id": str(application.job_offer_id),
        "worker_id": str(application.worker_id),
        "status": application.status,
        "match_score": None,
        "cover_note": application.cover_note,
        "applied_at": application.applied_at,
        "job_title": offer.title,
    }


@router.get("/applications")
async def get_my_applications(
    limit: int = 20,
    offset: int = 0,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    from app.models.application import Application
    from app.models.employer import Employer
    from app.models.job_offer import JobOffer

    limit = min(limit, 100)
    worker = await _get_worker_or_404(payload["sub"], db)

    apps_result = await db.execute(
        select(Application)
        .where(Application.worker_id == str(worker.id))
        .order_by(Application.applied_at.desc())
        .limit(limit)
        .offset(offset)
    )
    apps = apps_result.scalars().all()

    result = []
    for app in apps:
        offer_res = await db.execute(select(JobOffer).where(JobOffer.id == str(app.job_offer_id)))
        offer = offer_res.scalar_one_or_none()
        emp_name = ""
        if offer:
            emp_res = await db.execute(select(Employer).where(Employer.id == str(offer.employer_id)))
            emp = emp_res.scalar_one_or_none()
            emp_name = emp.company_name if emp else ""
        result.append({
            "id": str(app.id),
            "job_offer_id": str(app.job_offer_id),
            "job_title": offer.title if offer else "",
            "employer_name": emp_name,
            "status": app.status,
            "match_score": float(app.match_score) if app.match_score else None,
            "applied_at": app.applied_at,
        })

    return result
