# RF: RF118-RF125 (M07) — Servicio de marketplace de oficios con búsqueda semántica
from __future__ import annotations

import uuid
import structlog
from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_listing import ServiceListing
from app.models.worker import Worker
from app.nlp.embeddings.generator import apply_local_dictionary, generate_embedding
from app.nlp.portfolio_nlp.trade_extractor import extract_skills_from_job_description
from app.schemas.marketplace import (
    ServiceListingCreate,
    ServiceListingResponse,
    ServiceListingUpdate,
)

logger = structlog.get_logger()

AVAILABILITY_BOOST = {"inmediata": 1.0, "semana": 0.6, "mes": 0.3}


def _build_response(listing: ServiceListing, worker: Worker, score: float | None = None) -> ServiceListingResponse:
    full_name = ""
    try:
        from app.core.security import decrypt_field
        if worker.full_name:
            full_name = decrypt_field(worker.full_name)
    except Exception:
        full_name = ""

    return ServiceListingResponse(
        id=str(listing.id),
        worker_id=str(listing.worker_id),
        trade_category=listing.trade_category,
        title=listing.title,
        description=listing.description,
        enriched_keywords=listing.enriched_keywords or [],
        districts=listing.districts or [],
        price_reference=listing.price_reference,
        price_unit=listing.price_unit,
        availability=listing.availability,
        is_active=listing.is_active,
        views_count=listing.views_count or 0,
        created_at=listing.created_at,
        worker_name=full_name,
        worker_district=worker.district or "",
        worker_avg_rating=float(worker.avg_rating or 0),
        worker_years_experience=worker.years_experience or 0,
        worker_username=worker.username,
        relevance_score=score,
    )


async def create_listing(
    worker: Worker,
    body: ServiceListingCreate,
    db: AsyncSession,
) -> ServiceListingResponse:
    extraction = extract_skills_from_job_description(body.description, body.trade_category)
    enriched = list(set(extraction.skills))

    listing = ServiceListing(
        id=str(uuid.uuid4()),
        worker_id=str(worker.id),
        trade_category=body.trade_category,
        title=body.title,
        description=body.description,
        enriched_keywords=enriched,
        districts=body.districts,
        price_reference=body.price_reference,
        price_unit=body.price_unit,
        availability=body.availability or "inmediata",
        is_active=True,
        views_count=0,
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)

    # Generar embedding de forma asíncrona (Celery)
    try:
        from app.tasks.embeddings import generate_listing_embedding
        generate_listing_embedding.delay(str(listing.id))
    except Exception as exc:
        logger.warning("listing_embedding_task_failed", error=str(exc))

    logger.info("marketplace_listing_created", listing_id=str(listing.id), worker_id=str(worker.id))
    return _build_response(listing, worker)


async def update_listing(
    listing_id: str,
    worker_id: str,
    body: ServiceListingUpdate,
    db: AsyncSession,
) -> ServiceListingResponse:
    result = await db.execute(
        select(ServiceListing).where(
            ServiceListing.id == listing_id,
            ServiceListing.worker_id == worker_id,
        )
    )
    listing = result.scalar_one_or_none()
    if not listing:
        return None  # type: ignore[return-value]

    worker_res = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = worker_res.scalar_one_or_none()

    changes = body.model_dump(exclude_unset=True)
    re_embed = False
    for field, value in changes.items():
        setattr(listing, field, value)
        if field == "description":
            extraction = extract_skills_from_job_description(value, listing.trade_category)
            listing.enriched_keywords = list(set(extraction.skills))
            re_embed = True

    await db.commit()
    await db.refresh(listing)

    if re_embed:
        try:
            from app.tasks.embeddings import generate_listing_embedding
            generate_listing_embedding.delay(str(listing.id))
        except Exception:
            pass

    return _build_response(listing, worker)


async def get_listing(listing_id: str, db: AsyncSession) -> ServiceListingResponse | None:
    result = await db.execute(
        select(ServiceListing).where(ServiceListing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        return None

    worker_res = await db.execute(select(Worker).where(Worker.id == listing.worker_id))
    worker = worker_res.scalar_one_or_none()
    if not worker:
        return None

    listing.views_count = (listing.views_count or 0) + 1
    await db.commit()

    return _build_response(listing, worker)


async def search_listings(
    query: str | None,
    districts: list[str] | None,
    trade_category: str | None,
    availability: str | None,
    limit: int,
    offset: int,
    db: AsyncSession,
) -> list[ServiceListingResponse]:
    conditions = [ServiceListing.is_active.is_(True)]
    if districts:
        conditions.append(ServiceListing.districts.cast(text("text")).contains(districts[0]))
    if trade_category:
        conditions.append(ServiceListing.trade_category == trade_category)
    if availability:
        conditions.append(ServiceListing.availability == availability)

    if query:
        normalized = apply_local_dictionary(query)
        embedding = generate_embedding(normalized)
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

        # pgvector cosine similarity — fórmula: 0.5×cosine + 0.3×(rating/5) + 0.2×avail_boost
        sql = text(f"""
            SELECT
                sl.*,
                w.full_name, w.district AS w_district, w.avg_rating,
                w.years_experience, w.username,
                (
                    0.5 * (1 - (sl.embedding <=> '{embedding_str}'::vector))
                    + 0.3 * (COALESCE(w.avg_rating, 0) / 5.0)
                    + 0.2 * CASE sl.availability
                        WHEN 'inmediata' THEN 1.0
                        WHEN 'semana' THEN 0.6
                        ELSE 0.3
                    END
                ) AS relevance_score
            FROM service_listings sl
            JOIN workers w ON w.id = sl.worker_id
            WHERE sl.is_active = TRUE
                {(' AND sl.trade_category = :tc') if trade_category else ''}
                {(' AND sl.availability = :av') if availability else ''}
                AND sl.embedding IS NOT NULL
            ORDER BY relevance_score DESC
            LIMIT :limit OFFSET :offset
        """)

        params: dict = {"limit": limit, "offset": offset}
        if trade_category:
            params["tc"] = trade_category
        if availability:
            params["av"] = availability

        rows = (await db.execute(sql, params)).fetchall()

        results = []
        for row in rows:
            listing = ServiceListing(
                id=str(row.id),
                worker_id=str(row.worker_id),
                trade_category=row.trade_category,
                title=row.title,
                description=row.description,
                enriched_keywords=row.enriched_keywords or [],
                districts=row.districts or [],
                price_reference=row.price_reference,
                price_unit=row.price_unit,
                availability=row.availability,
                is_active=row.is_active,
                views_count=row.views_count or 0,
                created_at=row.created_at,
            )
            worker = Worker(
                id=str(row.worker_id),
                full_name=row.full_name,
                district=row.w_district,
                avg_rating=row.avg_rating,
                years_experience=row.years_experience,
                username=row.username,
                worker_type="oficio",
                dni=b"",
                user_id="",
            )
            results.append(_build_response(listing, worker, score=float(row.relevance_score or 0)))
        return results

    # Sin query — retornar por rating + disponibilidad
    stmt = (
        select(ServiceListing)
        .where(and_(*conditions))
        .order_by(ServiceListing.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    listings = (await db.execute(stmt)).scalars().all()

    results = []
    for listing in listings:
        worker_res = await db.execute(select(Worker).where(Worker.id == listing.worker_id))
        worker = worker_res.scalar_one_or_none()
        if worker:
            results.append(_build_response(listing, worker))
    return results


async def delete_listing(listing_id: str, worker_id: str, db: AsyncSession) -> bool:
    result = await db.execute(
        select(ServiceListing).where(
            ServiceListing.id == listing_id,
            ServiceListing.worker_id == worker_id,
        )
    )
    listing = result.scalar_one_or_none()
    if not listing:
        return False
    listing.is_active = False
    await db.commit()
    return True
