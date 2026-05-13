# RF: RF118-RF125 (M07) — Marketplace de servicios de oficio
import uuid as uuid_mod

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, require_role
from app.models.notification import Notification
from app.models.service_listing import ServiceListing
from app.models.worker import Worker
from app.schemas.marketplace import (
    ServiceListingCreate,
    ServiceListingResponse,
    ServiceListingUpdate,
)
from app.services.marketplace.marketplace_service import (
    create_listing,
    delete_listing,
    get_listing,
    search_listings,
    update_listing,
)


class ContactRequest(BaseModel):
    message: str = Field(..., min_length=10, max_length=500)

router = APIRouter(prefix="/marketplace", tags=["Marketplace de Oficios"])
logger = structlog.get_logger()


async def _get_oficio_worker(user_id: str, db: AsyncSession) -> Worker:
    result = await db.execute(select(Worker).where(Worker.user_id == user_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    if worker.worker_type != "oficio":
        raise HTTPException(
            status_code=403,
            detail="El marketplace es exclusivo para trabajadores de tipo 'oficio'",
        )
    return worker


@router.post("/listings", response_model=ServiceListingResponse, status_code=201)
async def create_service_listing(
    body: ServiceListingCreate,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> ServiceListingResponse:
    """Publica un nuevo servicio en el marketplace. Solo para OFICIO (RF118)."""
    worker = await _get_oficio_worker(payload["sub"], db)
    result = await create_listing(worker, body, db)
    logger.info("marketplace_post_created", worker_id=str(worker.id))
    return result


@router.get("/listings", response_model=list[ServiceListingResponse])
async def list_my_listings(
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceListingResponse]:
    """Lista los servicios publicados por el trabajador autenticado."""
    await _get_oficio_worker(payload["sub"], db)
    return await search_listings(
        query=None,
        districts=None,
        trade_category=None,
        availability=None,
        limit=100,
        offset=0,
        db=db,
    )


@router.get("/search", response_model=list[ServiceListingResponse])
async def search_marketplace(
    query: str | None = Query(None, max_length=300, description="Búsqueda semántica en lenguaje natural"),
    district: str | None = Query(None, description="Filtrar por distrito"),
    trade_category: str | None = Query(None, description="Filtrar por categoría de oficio"),
    availability: str | None = Query(None, pattern="^(inmediata|semana|mes)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceListingResponse]:
    """Búsqueda semántica en el marketplace (RF119–RF122).
    Formula: 0.5×cosine_sim + 0.3×(rating/5) + 0.2×availability_boost.
    """
    districts = [district] if district else None
    return await search_listings(
        query=query,
        districts=districts,
        trade_category=trade_category,
        availability=availability,
        limit=limit,
        offset=offset,
        db=db,
    )


@router.get("/listings/{listing_id}", response_model=ServiceListingResponse)
async def get_service_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
) -> ServiceListingResponse:
    """Obtiene detalle de un servicio. Incrementa views_count (RF123)."""
    listing = await get_listing(listing_id, db)
    if not listing:
        raise HTTPException(status_code=404, detail="Listado no encontrado")
    return listing


@router.patch("/listings/{listing_id}", response_model=ServiceListingResponse)
async def update_service_listing(
    listing_id: str,
    body: ServiceListingUpdate,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> ServiceListingResponse:
    """Actualiza un servicio del marketplace (RF124)."""
    worker = await _get_oficio_worker(payload["sub"], db)
    updated = await update_listing(listing_id, str(worker.id), body, db)
    if not updated:
        raise HTTPException(status_code=404, detail="Listado no encontrado o no pertenece al trabajador")
    return updated


@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_service_listing(
    listing_id: str,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Desactiva (soft delete) un servicio del marketplace (RF125)."""
    worker = await _get_oficio_worker(payload["sub"], db)
    deleted = await delete_listing(listing_id, str(worker.id), db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Listado no encontrado o no pertenece al trabajador")


@router.post("/listings/{listing_id}/contact", status_code=status.HTTP_201_CREATED)
async def contact_oficio_worker(
    listing_id: str,
    body: ContactRequest,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Envía un mensaje de contacto al trabajador de oficio dueño del listado.
    Persiste en notifications y publica por WebSocket vía Redis pub/sub.
    """
    # Obtener el listado
    listing_res = await db.execute(
        select(ServiceListing).where(ServiceListing.id == listing_id, ServiceListing.is_active.is_(True))
    )
    listing = listing_res.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listado no encontrado")

    # No permitir contactarse a uno mismo
    if listing.worker_id == payload["sub"]:
        raise HTTPException(status_code=400, detail="No puedes contactarte a ti mismo")

    # Obtener user_id del trabajador dueño del listado
    worker_res = await db.execute(
        select(Worker).where(Worker.id == listing.worker_id)
    )
    oficio_worker = worker_res.scalar_one_or_none()
    if not oficio_worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    # Persistir notificación
    notif = Notification(
        id=str(uuid_mod.uuid4()),
        user_id=oficio_worker.user_id,
        notification_type="message",
        title=f"Solicitud de contacto — {listing.title}",
        body=body.message,
        payload={"listing_id": listing_id, "sender_user_id": payload["sub"]},
    )
    db.add(notif)
    await db.commit()

    # Publicar por WebSocket (no-fail si Redis no está disponible)
    try:
        from app.api.v1.ws_notifications import publish_notification
        from app.core.redis_client import get_redis
        redis = get_redis()
        await publish_notification(
            user_id=oficio_worker.user_id,
            notification_type="message",
            title=f"Solicitud de contacto — {listing.title}",
            body=body.message,
            payload={"listing_id": listing_id, "sender_user_id": payload["sub"]},
            redis=redis,
        )
    except Exception as exc:
        logger.warning("contact_ws_publish_failed", error=str(exc))

    logger.info("contact_request_sent", listing_id=listing_id, sender=payload["sub"])
    return {"status": "sent", "worker_user_id": oficio_worker.user_id}
