# RF: RF086-RF095 (M05), RF146-RF150 (M10) — Celery tasks: reentrenamiento y drift ML
import asyncio

import structlog

from app.tasks import celery_app

logger = structlog.get_logger()

WORKER_TYPES = ["primer_empleo", "experiencia", "oficio", "all"]

# PSI alert threshold — debe coincidir con drift_detector.py
PSI_ALERT = 0.25


@celery_app.task(name="ml_tasks.retrain_model_if_needed", bind=True, max_retries=2)
def retrain_model_if_needed_task(self, worker_type: str = "all") -> dict:
    """Reentrenar solo si hay drift PSI ≥ 0.25 o el modelo aún no existe.

    Diseñado para ejecutarse desde un beat schedule periódico (diario).
    """
    from app.ml.matching_engine.drift_detector import check_all_types_drift

    try:
        drift_results = check_all_types_drift()
        needs_retrain = False

        if worker_type == "all":
            types_to_check = WORKER_TYPES
        else:
            types_to_check = [worker_type]

        for wtype in types_to_check:
            result = drift_results.get(wtype, {})
            status = result.get("status", "no_reference")
            if status in ("alert", "no_reference", "no_current"):
                needs_retrain = True
                logger.info("retrain_triggered_by_drift", worker_type=wtype, status=status)
                break

        if not needs_retrain:
            logger.info("no_retrain_needed", drift=drift_results)
            return {"retrained": False, "reason": "no_drift_detected"}

        return retrain_model_task(worker_type=worker_type)

    except Exception as exc:
        logger.error("retrain_check_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(name="ml_tasks.retrain_model", bind=True, max_retries=1)
def retrain_model_task(self, worker_type: str = "all") -> dict:
    """Reentrenamiento forzado desde match_events — no verifica drift."""

    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.ml.matching_engine.trainer import train_from_db

        async with AsyncSessionLocal() as db:
            return await train_from_db(db, worker_type=worker_type, deploy_if_better=True)

    try:
        result = asyncio.run(_run())
        logger.info(
            "retrain_completed",
            worker_type=worker_type,
            deployed=result.get("deployed"),
            metrics=result.get("metrics"),
        )
        return result
    except Exception as exc:
        logger.error("retrain_failed", worker_type=worker_type, error=str(exc))
        raise self.retry(exc=exc, countdown=600)
