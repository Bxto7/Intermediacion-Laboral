from celery import Celery

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
)

# Re-export celery_app alias for backwards compatibility
celery_app = app
