# RF: RF096-RF110 (M06) — generacion de CVs PDF
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, require_role
from app.models.worker import Worker

logger = structlog.get_logger()
router = APIRouter(prefix="/cv", tags=["cv"])


class GeneratedCVResponse(BaseModel):
    task_id: str
    status: str
    message: str = "CV en proceso de generacion"


class CVDownloadResponse(BaseModel):
    worker_id: str
    worker_type: str
    download_url: str | None = None
    message: str


@router.post("/generate/{worker_id}", response_model=GeneratedCVResponse)
async def generate_cv(
    worker_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WORKER)),
):
    """RF096-RF110: Genera CV PDF para el trabajador segun su tipo."""
    token_user_id = current_user.get("sub", "")

    res = await db.execute(select(Worker).where(Worker.id == str(worker_id)))
    worker = res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    if str(worker.user_id) != token_user_id:
        raise HTTPException(status_code=403, detail="No puedes generar CV de otro trabajador")

    from app.tasks.cv_generator import generate_cv_task
    task = generate_cv_task.delay(str(worker_id))

    return GeneratedCVResponse(
        task_id=task.id,
        status="processing",
        message=f"Generando CV tipo {worker.worker_type}. Te notificaremos cuando este listo.",
    )


@router.get("/download/{worker_id}")
async def download_cv(
    worker_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WORKER)),
):
    """Descarga el CV directamente (sincrono, para testing y desarrollo)."""
    token_user_id = current_user.get("sub", "")

    res = await db.execute(select(Worker).where(Worker.id == str(worker_id)))
    worker = res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    if str(worker.user_id) != token_user_id:
        raise HTTPException(status_code=403, detail="Sin permiso")

    from app.services.cv_builder.pdf_generator import generate_cv_pdf

    try:
        pdf_bytes = await generate_cv_pdf(worker_id, db)
    except Exception as exc:
        logger.error("cv_download_failed", worker_id=str(worker_id), error=str(exc))
        raise HTTPException(status_code=500, detail="Error generando el CV") from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cv_{worker.worker_type}.pdf"},
    )
