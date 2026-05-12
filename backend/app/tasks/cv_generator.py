# RF: RF096-RF110 (M06) — tarea Celery para generacion de CVs PDF
import uuid as uuid_mod

import structlog

from app.tasks import app

logger = structlog.get_logger()


@app.task(name="tasks.generate_cv", bind=True, max_retries=3, queue="cv_generation")
def generate_cv_task(self, worker_id: str):
    """Genera el CV PDF de forma asincrona y notifica al usuario."""
    try:
        validated_id = uuid_mod.UUID(worker_id, version=4)
    except ValueError:
        logger.error("invalid_uuid_cv_task", worker_id=worker_id)
        return {"status": "error", "reason": "invalid_uuid"}

    import asyncio

    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.services.cv_builder.pdf_generator import generate_cv_pdf

        async with AsyncSessionLocal() as db:
            pdf_bytes = await generate_cv_pdf(str(validated_id), db)
            logger.info(
                "cv_task_completed",
                worker_id=worker_id,
                size_bytes=len(pdf_bytes),
            )
            return {"status": "done", "size_bytes": len(pdf_bytes)}

    try:
        result = asyncio.run(_run())
        return result
    except Exception as exc:
        logger.error("cv_generation_failed", worker_id=worker_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)
