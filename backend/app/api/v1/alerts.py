# RF: RF111-RF117 (M07) — alertas configurables de empleo

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, require_role
from app.models.job_alert import JobAlert
from app.models.worker import Worker

logger = structlog.get_logger()
router = APIRouter(prefix="/alerts", tags=["alerts"])


class JobAlertCreate(BaseModel):
    keywords: list[str] = []
    districts: list[str] = []
    trade_categories: list[str] = []
    salary_min: float | None = None


class JobAlertResponse(BaseModel):
    id: str
    worker_type: str
    keywords: list
    districts: list
    trade_categories: list
    salary_min: float | None = None
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("", response_model=JobAlertResponse, status_code=201)
async def create_alert(
    body: JobAlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WORKER)),
):
    """RF111: Crea alerta configurable de empleo."""
    user_id = current_user.get("sub", "")
    res = await db.execute(select(Worker).where(Worker.user_id == user_id))
    worker = res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    from app.services.matching.job_alerts import create_job_alert
    alert = await create_job_alert(
        worker_id=worker.id,
        keywords=body.keywords,
        districts=body.districts,
        trade_categories=body.trade_categories,
        salary_min=body.salary_min,
        db=db,
    )
    return alert


@router.get("", response_model=list[JobAlertResponse])
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WORKER)),
):
    """Lista las alertas activas del trabajador autenticado."""
    user_id = current_user.get("sub", "")
    res = await db.execute(select(Worker).where(Worker.user_id == user_id))
    worker = res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    alert_res = await db.execute(
        select(JobAlert).where(JobAlert.worker_id == str(worker.id))
    )
    return list(alert_res.scalars().all())


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WORKER)),
):
    """Desactiva una alerta del trabajador."""
    user_id = current_user.get("sub", "")
    res = await db.execute(select(Worker).where(Worker.user_id == user_id))
    worker = res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    from app.services.matching.job_alerts import deactivate_job_alert
    deleted = await deactivate_job_alert(alert_id, str(worker.id), db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
