# RF: RF055
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, Request
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.employer import Employer
from app.models.job_offer import JobOffer
from app.models.search_log import SearchLog
from app.schemas.job_offer import JobOfferResponse

router = APIRouter(prefix="/jobs", tags=["Ofertas de Empleo"])
logger = structlog.get_logger()


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


@router.get("/feed", response_model=list[JobOfferResponse])
async def get_jobs_feed(
    request: Request,
    district: str | None = None,
    modality: str | None = None,
    worker_type_target: str | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[JobOfferResponse]:
    limit = min(limit, 100)
    now = datetime.now(tz=UTC)

    conditions = [
        JobOffer.is_active.is_(True),
        (JobOffer.expires_at.is_(None)) | (JobOffer.expires_at > now),
    ]

    if district:
        conditions.append(JobOffer.district == district)
    if modality:
        conditions.append(JobOffer.modality == modality)
    if worker_type_target:
        conditions.append(
            (JobOffer.worker_type_target == worker_type_target)
            | (JobOffer.worker_type_target == "cualquiera")
        )
    if salary_min is not None:
        conditions.append((JobOffer.salary_min.is_(None)) | (JobOffer.salary_min >= salary_min))
    if salary_max is not None:
        conditions.append((JobOffer.salary_max.is_(None)) | (JobOffer.salary_max <= salary_max))

    result = await db.execute(
        select(JobOffer)
        .where(and_(*conditions))
        .order_by(JobOffer.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    offers = result.scalars().all()

    query_text = str(request.query_params) if request.query_params else None
    searcher_id: str | None = None
    try:

        from app.core.security import verify_token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            tok = auth_header.split(" ", 1)[1]
            payload = await verify_token(tok)
            searcher_id = payload.get("sub")
    except Exception:
        logger.debug("anonymous_job_feed_request")

    log = SearchLog(
        searcher_id=searcher_id,
        query_text=query_text,
        results_count=len(offers),
        district_filter=district,
    )
    db.add(log)
    await db.commit()

    employer_ids = list({str(o.employer_id) for o in offers})
    employer_map: dict[str, str] = {}
    if employer_ids:
        emp_result = await db.execute(
            select(Employer).where(Employer.id.in_(employer_ids))
        )
        for emp in emp_result.scalars().all():
            employer_map[str(emp.id)] = emp.company_name

    return [_build_offer_response(o, employer_map.get(str(o.employer_id), "")) for o in offers]
