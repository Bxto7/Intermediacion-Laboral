from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

app = Celery(
    "intermediacion_laboral",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Lima",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_queues={
        "embeddings":    {"exchange": "embeddings",    "routing_key": "embeddings"},
        "cv_generation": {"exchange": "cv_generation", "routing_key": "cv_generation"},
        "notifications": {"exchange": "notifications", "routing_key": "notifications"},
        "reports":       {"exchange": "reports",       "routing_key": "reports"},
        "default":       {"exchange": "default",       "routing_key": "default"},
    },
    task_default_queue="default",
    task_routes={
        "tasks.generate_embedding":    {"queue": "embeddings"},
        "tasks.generate_cv":           {"queue": "cv_generation"},
        "tasks.send_notification":     {"queue": "notifications"},
        "tasks.generate_report":       {"queue": "reports"},
        "tasks.process_job_alerts":    {"queue": "default"},
        "tasks.reindex_marketplace":   {"queue": "embeddings"},
    },
    beat_schedule={
        "regenerate-stale-embeddings": {
            "task": "tasks.regenerate_stale_embeddings",
            "schedule": crontab(hour=2, minute=0),
            "kwargs": {"max_age_days": 7},
        },
        "process-job-alerts": {
            "task": "tasks.process_all_job_alerts",
            "schedule": crontab(minute=0),
        },
        "calculate-kpis": {
            "task": "tasks.calculate_kpis",
            "schedule": crontab(hour=6, minute=0),
        },
        "reindex-marketplace": {
            "task": "tasks.reindex_listings",
            "schedule": crontab(hour=3, minute=0),
        },
        "retrain-matching-model": {
            "task": "tasks.retrain_model_if_needed",
            "schedule": crontab(hour=4, minute=0, day_of_week=1),
        },
        "cleanup-expired-tokens": {
            "task": "tasks.cleanup_expired_tokens",
            "schedule": crontab(hour=1, minute=0),
        },
    },
)

# Re-export alias
celery_app = app
