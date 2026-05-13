# RF: RF016-RF022
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_field
from app.models.audit_log import AuditLog
from app.models.worker import Worker
from app.schemas.common import TradeCategory, WorkerType
from app.schemas.onboarding import OnboardingAnswers

logger = structlog.get_logger()


def detect_worker_type(answers: OnboardingAnswers) -> WorkerType:
    if answers.is_first_job:
        return WorkerType.PRIMER_EMPLEO
    if answers.is_trade_worker:
        return WorkerType.OFICIO
    return WorkerType.EXPERIENCIA


async def _generate_unique_username(base: str, db: AsyncSession) -> str:
    import re
    import unicodedata

    from sqlalchemy import select

    # Normalize unicode → remove accents → lowercase → replace non-alphanumeric with hyphens
    normalized = unicodedata.normalize("NFKD", base or "usuario")
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_str.lower()).strip("-")[:40] or "usuario"
    candidate = slug
    counter = 1
    while True:
        result = await db.execute(select(Worker).where(Worker.username == candidate))
        if not result.scalar_one_or_none():
            return candidate
        candidate = f"{slug}{counter}"
        counter += 1


async def create_worker_profile(
    user_id: str,
    worker_type: WorkerType,
    trade_category: TradeCategory | None,
    db: AsyncSession,
) -> Worker:
    from app.core.redis_client import get_redis

    redis = get_redis()
    identity_raw = await redis.get(f"reg_identity:{user_id}")
    full_name_plain = "pendiente"
    dni_plain = "00000000"
    if identity_raw:
        parts = identity_raw.split("|", 1)
        if len(parts) == 2:
            full_name_plain = parts[0] or "pendiente"
            dni_plain = parts[1] or "00000000"
        await redis.delete(f"reg_identity:{user_id}")

    username = await _generate_unique_username(f"usuario{user_id[:6]}", db)
    worker = Worker(
        user_id=user_id,
        worker_type=worker_type.value,
        full_name=encrypt_field(full_name_plain),
        dni=encrypt_field(dni_plain),
        trade_category=trade_category.value if trade_category else None,
        profile_completeness=0,
        username=username,
    )
    db.add(worker)
    await db.flush()

    audit = AuditLog(
        user_id=user_id,
        action="worker_profile_created",
        entity_type="worker",
        entity_id=worker.id,
        details={"worker_type": worker_type.value},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(worker)

    logger.info(
        "worker_profile_created",
        worker_id=worker.id,
        worker_type=worker_type.value,
    )
    return worker


def get_next_step_url(worker_type: WorkerType) -> str:
    urls = {
        WorkerType.PRIMER_EMPLEO: "/onboarding/primer-empleo/wizard",
        WorkerType.EXPERIENCIA: "/perfil/experiencia",
        WorkerType.OFICIO: "/oficio/portfolio",
    }
    return urls[worker_type]
