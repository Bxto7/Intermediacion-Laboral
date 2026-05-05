from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "intermediacion_laboral",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.embeddings",
        "app.tasks.reports",
        "app.tasks.emails",
        "app.tasks.notifications",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Lima",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
    task_routes={
        "app.tasks.embeddings.*": {"queue": "embeddings"},
        "app.tasks.reports.*": {"queue": "reports"},
        "app.tasks.emails.*": {"queue": "emails"},
        "app.tasks.notifications.*": {"queue": "notifications"},
    },
    beat_schedule={
        "regenerate-stale-embeddings": {
            "task": "app.tasks.embeddings.regenerate_stale",
            "schedule": 3600.0,
        },
        "send-post-survey-reminders": {
            "task": "app.tasks.emails.send_post_survey_reminders",
            "schedule": 86400.0,
        },
    },
)
