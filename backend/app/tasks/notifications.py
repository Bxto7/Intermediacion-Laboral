# RF: RNF003 (stub Sprint 1)
import structlog

from app.tasks import app

logger = structlog.get_logger()


@app.task(name="send_reset_email")
def send_reset_email(user_id: str, token: str) -> None:
    logger.info("reset_email_queued", user_id=user_id)


@app.task(name="send_push_notification", queue="notifications")
def send_push_notification(user_id: str, title: str, body: str) -> dict:
    logger.info("push_notification_queued", user_id=user_id)
    return {"status": "queued"}


@app.task(name="notify_employer_new_application", queue="notifications")
def notify_employer_new_application(employer_id: str, job_offer_id: str, worker_id: str) -> dict:
    logger.info(
        "notify_employer_new_application_queued",
        employer_id=employer_id,
        job_offer_id=job_offer_id,
        worker_id=worker_id,
    )
    return {"status": "queued"}


@app.task(name="notify_worker_hired", queue="notifications")
def notify_worker_hired(worker_id: str, job_offer_id: str) -> dict:
    logger.info(
        "notify_worker_hired_queued",
        worker_id=worker_id,
        job_offer_id=job_offer_id,
    )
    return {"status": "queued"}
