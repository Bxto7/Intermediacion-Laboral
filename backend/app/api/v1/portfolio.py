# RF: RF056-RF065
from decimal import Decimal
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, decrypt_field, require_role
from app.models.portfolio import PortfolioEntry
from app.models.worker import Worker
from app.nlp.portfolio_nlp.trade_extractor import extract_skills_from_job_description
from app.schemas.portfolio import (
    PortfolioEntryCreate,
    PortfolioEntryResponse,
    PortfolioEntryUpdate,
    PublicPortfolioEntryResponse,
)
from app.tasks.embeddings import generate_portfolio_entry_embedding, generate_worker_embedding

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])
logger = structlog.get_logger()

ALLOWED_PHOTO_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTO_SIZE = 5 * 1024 * 1024


def _build_entry_response(entry: PortfolioEntry) -> PortfolioEntryResponse:
    return PortfolioEntryResponse(
        id=str(entry.id),
        worker_id=str(entry.worker_id),
        title=entry.title,
        description=entry.description,
        extracted_skills=entry.extracted_skills or [],
        photos=entry.photos or [],
        period_start=entry.period_start,
        period_end=entry.period_end,
        client_rating=float(entry.client_rating) if entry.client_rating else None,
        is_public=entry.is_public,
        created_at=entry.created_at,
    )


def _build_public_entry_response(entry: PortfolioEntry) -> PublicPortfolioEntryResponse:
    """Build public portfolio entry response without exposing worker_id UUID."""
    return PublicPortfolioEntryResponse(
        id=str(entry.id),
        title=entry.title,
        description=entry.description,
        extracted_skills=entry.extracted_skills or [],
        photos=entry.photos or [],
        period_start=entry.period_start,
        period_end=entry.period_end,
        client_rating=float(entry.client_rating) if entry.client_rating else None,
        is_public=entry.is_public,
        created_at=entry.created_at,
    )


async def _get_oficio_worker(user_id: str, db: AsyncSession) -> Worker:
    result = await db.execute(select(Worker).where(Worker.user_id == user_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")
    if worker.worker_type != "oficio":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El portfolio es exclusivo para trabajadores de tipo 'oficio'",
        )
    return worker


async def _recalculate_avg_rating(worker: Worker, db: AsyncSession) -> None:
    result = await db.execute(
        select(PortfolioEntry.client_rating)
        .where(
            PortfolioEntry.worker_id == str(worker.id),
            PortfolioEntry.client_rating.isnot(None),
        )
    )
    ratings = [r for (r,) in result.all() if r is not None]
    if ratings:
        avg = sum(float(r) for r in ratings) / len(ratings)
        worker.avg_rating = Decimal(str(round(avg, 2)))
    else:
        worker.avg_rating = Decimal("0.00")


@router.post("/entries", response_model=PortfolioEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio_entry(
    body: PortfolioEntryCreate,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> PortfolioEntryResponse:
    worker = await _get_oficio_worker(payload["sub"], db)

    trade_category = worker.trade_category or "Otros"
    extraction = extract_skills_from_job_description(body.description, trade_category)

    entry = PortfolioEntry(
        worker_id=str(worker.id),
        title=body.title,
        description=body.description,
        extracted_skills=extraction.skills,
        photos=[],
        period_start=body.period_start,
        period_end=body.period_end,
        client_rating=Decimal(str(body.client_rating)) if body.client_rating else None,
        is_public=body.is_public,
    )
    db.add(entry)
    await db.flush()

    if body.client_rating:
        await _recalculate_avg_rating(worker, db)

    await db.commit()
    await db.refresh(entry)

    generate_portfolio_entry_embedding.delay(str(entry.id))
    generate_worker_embedding.delay(str(worker.id))
    logger.info("portfolio_entry_created", entry_id=str(entry.id), worker_id=str(worker.id))

    return _build_entry_response(entry)


@router.get("/entries", response_model=list[PortfolioEntryResponse])
async def list_portfolio_entries(
    limit: int = 20,
    offset: int = 0,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> list[PortfolioEntryResponse]:
    limit = min(limit, 100)
    result = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")

    entries_result = await db.execute(
        select(PortfolioEntry)
        .where(PortfolioEntry.worker_id == str(worker.id))
        .order_by(PortfolioEntry.period_end.desc().nullslast(), PortfolioEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_build_entry_response(e) for e in entries_result.scalars().all()]


@router.get("/{username}", response_model=dict)
async def get_public_portfolio(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Worker).where(Worker.username == username, Worker.worker_type == "oficio")
    )
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio no encontrado")

    full_name = ""
    try:
        full_name = decrypt_field(worker.full_name) if worker.full_name else ""
    except Exception:
        full_name = ""

    entries_result = await db.execute(
        select(PortfolioEntry)
        .where(PortfolioEntry.worker_id == str(worker.id), PortfolioEntry.is_public.is_(True))
        .order_by(PortfolioEntry.created_at.desc())
    )
    # Use PublicPortfolioEntryResponse to exclude worker_id UUID (RNF001 audit)
    entries = [_build_public_entry_response(e) for e in entries_result.scalars().all()]

    return {
        "full_name": full_name,
        "trade_category": worker.trade_category,
        "district": worker.district,
        "avg_rating": float(worker.avg_rating or 0),
        "is_available": worker.is_available,
        "entries": [e.model_dump() for e in entries],
    }


@router.patch("/entries/{entry_id}", response_model=PortfolioEntryResponse)
async def update_portfolio_entry(
    entry_id: str,
    body: PortfolioEntryUpdate,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> PortfolioEntryResponse:
    result = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")

    entry_result = await db.execute(
        select(PortfolioEntry).where(
            PortfolioEntry.id == entry_id,
            PortfolioEntry.worker_id == str(worker.id),
        )
    )
    entry = entry_result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrada no encontrada")

    update_data = body.model_dump(exclude_unset=True)
    re_embed = False

    for field, value in update_data.items():
        if field == "client_rating":
            entry.client_rating = Decimal(str(value)) if value else None
        else:
            setattr(entry, field, value)
        if field == "description":
            trade_category = worker.trade_category or "Otros"
            extraction = extract_skills_from_job_description(value, trade_category)
            entry.extracted_skills = extraction.skills
            re_embed = True

    if update_data.get("client_rating") is not None:
        await _recalculate_avg_rating(worker, db)

    await db.commit()
    await db.refresh(entry)

    if re_embed:
        generate_portfolio_entry_embedding.delay(str(entry.id))
        generate_worker_embedding.delay(str(worker.id))

    return _build_entry_response(entry)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_entry(
    entry_id: str,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")

    entry_result = await db.execute(
        select(PortfolioEntry).where(
            PortfolioEntry.id == entry_id,
            PortfolioEntry.worker_id == str(worker.id),
        )
    )
    entry = entry_result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrada no encontrada")

    await db.delete(entry)
    await _recalculate_avg_rating(worker, db)
    await db.commit()

    generate_worker_embedding.delay(str(worker.id))


@router.post("/entries/{entry_id}/photos", response_model=list[str])
async def upload_portfolio_photos(
    entry_id: str,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    if len(files) > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximo 5 fotos por entrada")

    result = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")

    entry_result = await db.execute(
        select(PortfolioEntry).where(
            PortfolioEntry.id == entry_id,
            PortfolioEntry.worker_id == str(worker.id),
        )
    )
    entry = entry_result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrada no encontrada")

    from app.core.config import settings

    new_urls: list[str] = []
    for f in files:
        if f.content_type not in ALLOWED_PHOTO_MIME:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Tipo de archivo no permitido: {f.content_type}. Solo JPEG, PNG o WEBP.",
            )
        content = await f.read()
        if len(content) > MAX_PHOTO_SIZE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"La foto '{f.filename}' supera el limite de 5 MB",
            )

        if settings.ENVIRONMENT == "development":
            save_dir = Path(f"/tmp/portfolio_photos/{entry_id}")  # noqa: S108
            save_dir.mkdir(parents=True, exist_ok=True)
            safe_name = f.filename or "photo.jpg"
            file_path = save_dir / safe_name
            file_path.write_bytes(content)
            url = f"http://localhost:8000/static/{entry_id}/{safe_name}"
        else:
            # TODO: Sprint 4 — upload to GCS/S3 using google-cloud-storage or boto3
            url = f"http://localhost:8000/static/{entry_id}/{f.filename}"

        new_urls.append(url)

    existing = list(entry.photos or [])
    existing.extend(new_urls)
    entry.photos = existing
    await db.commit()

    logger.info("portfolio_photos_uploaded", entry_id=entry_id, count=len(new_urls))
    return new_urls


class _ContactBody(BaseModel):
    message: str = Field(..., min_length=10, max_length=500)


@router.post("/{username}/contact", status_code=status.HTTP_201_CREATED)
async def contact_portfolio_worker(
    username: str,
    body: _ContactBody,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Envía mensaje de contacto al trabajador de oficio dueño del portfolio (RF123)."""
    import uuid as uuid_mod

    result = await db.execute(
        select(Worker).where(Worker.username == username, Worker.worker_type == "oficio")
    )
    oficio_worker = result.scalar_one_or_none()
    if not oficio_worker:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")

    if str(oficio_worker.user_id) == payload["sub"]:
        raise HTTPException(status_code=400, detail="No puedes contactarte a ti mismo")

    from app.models.notification import Notification

    notif = Notification(
        id=str(uuid_mod.uuid4()),
        user_id=oficio_worker.user_id,
        notification_type="message",
        title=f"Solicitud de contacto — Portfolio de {username}",
        body=body.message,
        payload={"portfolio_username": username, "sender_user_id": payload["sub"]},
    )
    db.add(notif)
    await db.commit()

    try:
        from app.api.v1.ws_notifications import publish_notification
        from app.core.redis_client import get_redis

        redis = get_redis()
        await publish_notification(
            user_id=oficio_worker.user_id,
            notification_type="message",
            title=f"Solicitud de contacto — Portfolio de {username}",
            body=body.message,
            payload={"portfolio_username": username, "sender_user_id": payload["sub"]},
            redis=redis,
        )
    except Exception as exc:
        logger.warning("contact_portfolio_ws_publish_failed", error=str(exc))

    logger.info("portfolio_contact_sent", username=username, sender=payload["sub"])
    return {"status": "sent", "worker_user_id": str(oficio_worker.user_id)}
