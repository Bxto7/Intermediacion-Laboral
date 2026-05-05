import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.emails.send_verification_email", queue="emails")
def send_verification_email(user_id: str, email: str) -> dict:
    logger.info("send_verification_email_queued", user_id=user_id)
    return {"status": "queued"}


@celery_app.task(name="app.tasks.emails.send_post_survey_reminders", queue="emails")
def send_post_survey_reminders() -> dict:
    logger.info("post_survey_reminders_started")
    return {"status": "ok"}
