# RF: RF059-RF079
import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import check_rate_limit
from app.core.redis_client import get_redis
from app.core.security import UserRole, require_role
from app.models.worker import Worker
from app.nlp.cv_parser.parser import extract_cv_fields, parse_docx, parse_pdf
from app.nlp.portfolio_nlp.trade_extractor import extract_skills_from_job_description
from app.nlp.skill_extractor.first_job_extractor import (
    extract_skills_from_wizard_answer,
    suggest_job_sectors,
)
from app.schemas.cv import ParsedCVResult
from app.tasks.embeddings import generate_worker_embedding

router = APIRouter(prefix="/nlp", tags=["NLP"])
logger = structlog.get_logger()

ALLOWED_CV_MIME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


async def _get_worker_or_403(user_id: str, required_type: str, db: AsyncSession) -> Worker:
    result = await db.execute(select(Worker).where(Worker.user_id == user_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de trabajador no encontrado")
    if required_type and worker.worker_type != required_type:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Este endpoint es solo para trabajadores de tipo '{required_type}'",
        )
    return worker


@router.post("/extract-skills/wizard")
async def extract_wizard_skills(
    request: Request,
    body: dict,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    redis = get_redis()
    user_id = payload["sub"]
    await check_rate_limit(f"rl:nlp:wizard:{user_id}", 60, 60, redis)

    await _get_worker_or_403(user_id, "primer_empleo", db)

    step = body.get("step", 3)
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El campo 'text' es requerido")

    skills = extract_skills_from_wizard_answer(text, step)
    suggested_sectors = suggest_job_sectors(skills)

    return {"skills": skills, "suggested_sectors": suggested_sectors}


@router.post("/parse-cv", response_model=ParsedCVResult)
async def parse_cv(
    payload: dict = Depends(require_role(UserRole.WORKER)),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ParsedCVResult:
    await _get_worker_or_403(payload["sub"], "experiencia", db)

    if file.content_type not in ALLOWED_CV_MIME:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se aceptan archivos PDF o DOCX",
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo no debe superar 10 MB",
        )

    if file.content_type == "application/pdf":
        raw_text = parse_pdf(content)
    else:
        raw_text = parse_docx(content)

    if len(raw_text.strip()) < 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No se pudo extraer texto del archivo. "
                "Intenta con un PDF que no sea escaneado, "
                "o ingresa tu informacion manualmente."
            ),
        )

    result = extract_cv_fields(raw_text)
    logger.info("cv_parsed", user_id=payload["sub"], raw_length=result.raw_text_length)
    return result


@router.post("/extract-skills/portfolio")
async def extract_portfolio_skills(
    request: Request,
    body: dict,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    redis = get_redis()
    user_id = payload["sub"]
    await check_rate_limit(f"rl:nlp:portfolio:{user_id}", 30, 60, redis)

    await _get_worker_or_403(user_id, "oficio", db)

    description = body.get("description", "")
    trade_category = body.get("trade_category", "")
    if not description or not trade_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requieren 'description' y 'trade_category'",
        )

    extraction = extract_skills_from_job_description(description, trade_category)
    return {
        "skills": extraction.skills,
        "estimated_level": extraction.estimated_level,
        "confidence": extraction.confidence,
    }


@router.post("/worker/{worker_id}/regenerate-embedding")
async def regenerate_worker_embedding(
    worker_id: str,
    payload: dict = Depends(require_role(UserRole.ADMIN)),
) -> dict:
    generate_worker_embedding.delay(worker_id)
    logger.info("embedding_regeneration_queued", worker_id=worker_id, admin=payload["sub"])
    return {"queued": True, "worker_id": worker_id}


@router.get("/worker/{worker_id}/embedding-status")
async def get_embedding_status(
    worker_id: str,
    payload: dict = Depends(require_role(UserRole.ADMIN, UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if payload.get("role") == UserRole.WORKER.value:
        result = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
        worker = result.scalar_one_or_none()
        if not worker or str(worker.id) != worker_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    else:
        result = await db.execute(select(Worker).where(Worker.id == worker_id))
        worker = result.scalar_one_or_none()

    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trabajador no encontrado")

    return {
        "has_embedding": worker.embedding is not None,
        "profile_completeness": worker.profile_completeness or 0,
        "last_updated": worker.updated_at,
    }
