import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.reports.generate_research_dataset", queue="reports")
def generate_research_dataset(period_start: str, period_end: str) -> dict:
    logger.info("research_dataset_generation_started")
    return {"status": "queued"}
