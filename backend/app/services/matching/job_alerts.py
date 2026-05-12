# RF: RF111-RF117 (M07) — alertas configurables de empleo
import uuid as uuid_mod
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_alert import JobAlert
from app.models.worker import Worker

logger = structlog.get_logger()


async def create_job_alert(
    worker_id: UUID | str,
    keywords: list[str],
    districts: list[str],
    trade_categories: list[str],
    salary_min: float | None,
    db: AsyncSession,
) -> JobAlert:
    """RF111: Crea una alerta configurable de empleo para el trabajador."""
    res = await db.execute(select(Worker).where(Worker.id == str(worker_id)))
    worker = res.scalar_one_or_none()
    if not worker:
        raise ValueError(f"Worker {worker_id} no encontrado")

    alert = JobAlert(
        id=str(uuid_mod.uuid4()),
        worker_id=str(worker_id),
        worker_type=worker.worker_type,
        keywords=keywords,
        districts=districts,
        trade_categories=trade_categories,
        salary_min=salary_min,
        is_active=True,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    logger.info("job_alert_created", worker_id=str(worker_id), keywords=keywords)
    return alert


async def list_job_alerts(worker_id: UUID | str, db: AsyncSession) -> list[JobAlert]:
    """Lista todas las alertas activas del trabajador."""
    res = await db.execute(
        select(JobAlert).where(JobAlert.worker_id == str(worker_id))
    )
    return list(res.scalars().all())


async def deactivate_job_alert(alert_id: str, worker_id: str, db: AsyncSession) -> bool:
    """Desactiva una alerta del trabajador."""
    res = await db.execute(
        select(JobAlert).where(
            JobAlert.id == alert_id, JobAlert.worker_id == worker_id
        )
    )
    alert = res.scalar_one_or_none()
    if not alert:
        return False
    alert.is_active = False
    await db.commit()
    return True


async def process_alerts_for_new_offer(
    offer,
    db: AsyncSession,
    redis,
) -> None:
    """
    Verifica alertas activas contra una nueva oferta y publica notificaciones.
    Llamar desde el endpoint de publicacion de oferta.
    """
    from app.api.v1.ws_notifications import publish_notification
    from app.models.notification import Notification

    res = await db.execute(select(JobAlert).where(JobAlert.is_active.is_(True)))
    alerts = res.scalars().all()

    for alert in alerts:
        if not _alert_matches_offer(alert, offer):
            continue

        # Obtener user_id del worker
        worker_res = await db.execute(
            select(Worker).where(Worker.id == alert.worker_id)
        )
        worker = worker_res.scalar_one_or_none()
        if not worker:
            continue

        notif = Notification(
            id=str(uuid_mod.uuid4()),
            user_id=worker.user_id,
            worker_type=alert.worker_type,
            notification_type="alert_job",
            title="Nueva oferta que podria interesarte",
            body=f"Se publico: {offer.title} en {offer.district or 'tu zona'}",
            payload={"job_id": str(offer.id)},
        )
        db.add(notif)

        try:
            await publish_notification(
                user_id=worker.user_id,
                notification_type="alert_job",
                title="Nueva oferta disponible",
                body=f"{offer.title} · {offer.district or ''}",
                payload={"job_id": str(offer.id)},
                redis=redis,
            )
        except Exception as exc:
            logger.warning("alert_publish_failed", error=str(exc))

    await db.commit()


def _alert_matches_offer(alert: JobAlert, offer) -> bool:
    """Verifica si una oferta coincide con los criterios de una alerta."""
    if alert.keywords:
        offer_text = f"{getattr(offer, 'title', '')} {getattr(offer, 'description', '')}".lower()
        if not any(kw.lower() in offer_text for kw in alert.keywords):
            return False

    if alert.districts:
        offer_district = getattr(offer, "district", None)
        if offer_district and offer_district not in alert.districts:
            return False

    if alert.trade_categories:
        offer_cat = getattr(offer, "trade_category", None)
        if offer_cat and offer_cat not in alert.trade_categories:
            return False

    if alert.salary_min:
        offer_salary = getattr(offer, "salary_min", None)
        if offer_salary is not None and float(offer_salary) < float(alert.salary_min):
            return False

    return True
