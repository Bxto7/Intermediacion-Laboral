# RF: RF096-RF105 (M06) — cold-start por tipo de usuario
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


async def resolve_cold_start(worker, db: AsyncSession):
    """
    Genera embedding inicial para trabajadores sin historial.
    Diferenciado por worker_type: usa wizard (primer_empleo) o portfolio (oficio).
    """
    worker_type = worker.worker_type

    if worker_type == "primer_empleo":
        profile_text = await _build_first_job_text(worker, db)
    elif worker_type == "oficio":
        profile_text = await _build_trade_text(worker, db)
    else:
        profile_text = _build_experiencia_text(worker)

    try:
        embedding = generate_embedding_sync(profile_text)
        worker.embedding = embedding
        logger.info(
            "cold_start_embedding_generated",
            worker_id=str(worker.id),
            worker_type=worker_type,
        )
    except Exception as exc:
        logger.error("cold_start_failed", worker_id=str(worker.id), error=str(exc))

    return worker


async def _build_first_job_text(worker, db: AsyncSession) -> str:
    from app.models.wizard import WizardProgress

    res = await db.execute(
        select(WizardProgress).where(WizardProgress.worker_id == str(worker.id))
    )
    progress = res.scalar_one_or_none()

    skills = []
    interests = ""
    if progress:
        skills = list(progress.extracted_skills or [])
        answers = progress.answers or {}
        interests = answers.get("job_interests", "")

    parts = [f"primer empleo | {worker.district or 'Junin'}"]
    if skills:
        parts.append(f"habilidades: {', '.join(skills)}")
    if interests:
        parts.append(f"intereses: {interests}")
    return " | ".join(parts)


async def _build_trade_text(worker, db: AsyncSession) -> str:
    from app.models.portfolio import PortfolioEntry

    res = await db.execute(
        select(PortfolioEntry).where(PortfolioEntry.worker_id == str(worker.id))
    )
    entries = res.scalars().all()

    all_skills: list[str] = []
    for entry in entries:
        all_skills.extend(entry.extracted_skills or [])

    category = worker.trade_category or "oficio"
    years = worker.years_experience or 0
    district = worker.district or "Junin"
    skills_str = ", ".join(set(all_skills)) if all_skills else "sin habilidades registradas"

    return (
        f"{category} | {years} años | {district} | "
        f"habilidades: {skills_str} | trabajos: {len(entries)}"
    )


def _build_experiencia_text(worker) -> str:
    bio = getattr(worker, "bio", "") or ""
    job_title = getattr(worker, "job_title", "") or ""
    years = worker.years_experience or 0
    district = worker.district or "Junin"
    return f"{job_title} | {years} años | {district} | {bio}"


def generate_embedding_sync(text: str) -> list[float]:
    """Genera embedding sincrono desde texto de perfil."""
    from app.nlp.embeddings.generator import _get_model

    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()
