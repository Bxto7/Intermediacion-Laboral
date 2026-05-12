# RF: RNF009-RNF010 (storage GCS), RF096-RF110 (cv task), RF086-RF095/RF146-RF150 (ml tasks)
"""Tests de cobertura para storage GCS, tarea Celery de CV y tareas ML."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_bucket():
    bucket = MagicMock()
    blob = MagicMock()
    bucket.blob.return_value = blob
    blob.generate_signed_url.return_value = "https://storage.googleapis.com/signed"
    return bucket, blob


# ── app/services/storage.py ───────────────────────────────────────────────────

def test_upload_file_returns_path():
    from app.services.storage import upload_file
    bucket, blob = _mock_bucket()
    with patch("app.services.storage._get_bucket", return_value=bucket):
        result = upload_file(b"data", "portfolio/w1/file.jpg", "image/jpeg")
    assert result == "portfolio/w1/file.jpg"
    blob.upload_from_string.assert_called_once_with(b"data", content_type="image/jpeg")


def test_generate_signed_url_returns_url():
    from app.services.storage import generate_signed_url
    bucket, blob = _mock_bucket()
    with patch("app.services.storage._get_bucket", return_value=bucket):
        url = generate_signed_url("portfolio/w1/file.jpg")
    assert url == "https://storage.googleapis.com/signed"


def test_delete_file_calls_blob_delete():
    from app.services.storage import delete_file
    bucket, blob = _mock_bucket()
    with patch("app.services.storage._get_bucket", return_value=bucket):
        delete_file("portfolio/w1/file.jpg")
    blob.delete.assert_called_once()


def test_upload_portfolio_photo_size_exceeded():
    from app.services.storage import MAX_PHOTO_BYTES, upload_portfolio_photo
    content = b"x" * (MAX_PHOTO_BYTES + 1)
    with pytest.raises(ValueError, match="excede"):
        upload_portfolio_photo(content, "worker-1", "photo.jpg")


def test_upload_portfolio_photo_invalid_mime():
    from app.services.storage import upload_portfolio_photo
    with pytest.raises(ValueError, match="no permitido"):
        upload_portfolio_photo(b"data", "worker-1", "script.exe")


def test_upload_portfolio_photo_success():
    from app.services.storage import upload_portfolio_photo
    bucket, blob = _mock_bucket()
    with patch("app.services.storage._get_bucket", return_value=bucket):
        result = upload_portfolio_photo(b"x" * 100, "worker-1", "photo.jpg")
    assert result.startswith("portfolio/worker-1/")
    assert result.endswith(".jpg")


def test_upload_portfolio_photo_png():
    from app.services.storage import upload_portfolio_photo
    bucket, blob = _mock_bucket()
    with patch("app.services.storage._get_bucket", return_value=bucket):
        result = upload_portfolio_photo(b"x" * 100, "worker-2", "image.png")
    assert result.endswith(".png")


def test_upload_generated_cv_success():
    from app.services.storage import upload_generated_cv
    bucket, blob = _mock_bucket()
    with patch("app.services.storage._get_bucket", return_value=bucket):
        result = upload_generated_cv(b"pdf_bytes", "worker-3")
    assert result.startswith("cvs/worker-3/")
    assert result.endswith(".pdf")


# ── app/tasks/cv_generator.py ─────────────────────────────────────────────────
# Celery inyecta `self` (task instance) automáticamente en .run(); no hay que pasarlo.

def test_cv_task_invalid_uuid_returns_error():
    from app.tasks.cv_generator import generate_cv_task
    result = generate_cv_task.run("not-a-valid-uuid")
    assert result["status"] == "error"
    assert result["reason"] == "invalid_uuid"


def test_cv_task_valid_uuid_success():
    from app.tasks.cv_generator import generate_cv_task
    worker_id = str(uuid.uuid4())
    with patch("asyncio.run", return_value={"status": "done", "size_bytes": 500}):
        result = generate_cv_task.run(worker_id)
    assert result["status"] == "done"
    assert result["size_bytes"] == 500


def test_cv_task_exception_calls_retry():
    from app.tasks.cv_generator import generate_cv_task
    worker_id = str(uuid.uuid4())
    with patch("asyncio.run", side_effect=Exception("db_down")), \
         patch.object(generate_cv_task, "retry", side_effect=RuntimeError("retry_raised")), \
         pytest.raises(RuntimeError, match="retry_raised"):
        generate_cv_task.run(worker_id)


# ── app/tasks/ml_tasks.py ────────────────────────────────────────────────────

def test_retrain_model_task_success():
    from app.tasks.ml_tasks import retrain_model_task
    retrain_result = {"deployed": True, "metrics": {"f1": 0.81}}
    with patch("asyncio.run", return_value=retrain_result):
        result = retrain_model_task.run(worker_type="all")
    assert result["deployed"] is True


def test_retrain_model_task_exception_retries():
    from app.tasks.ml_tasks import retrain_model_task
    with patch("asyncio.run", side_effect=Exception("db_error")), \
         patch.object(retrain_model_task, "retry", side_effect=RuntimeError("retry_raised")), \
         pytest.raises(RuntimeError, match="retry_raised"):
        retrain_model_task.run(worker_type="oficio")


def test_retrain_if_needed_no_drift_detected():
    from app.tasks.ml_tasks import retrain_model_if_needed_task
    drift_ok = {
        "primer_empleo": {"status": "ok"},
        "experiencia": {"status": "ok"},
        "oficio": {"status": "warning"},
        "all": {"status": "ok"},
    }
    with patch("app.ml.matching_engine.drift_detector.check_all_types_drift", return_value=drift_ok):
        result = retrain_model_if_needed_task.run(worker_type="all")
    assert result["retrained"] is False
    assert result["reason"] == "no_drift_detected"


def test_retrain_if_needed_alert_triggers_retrain():
    from app.tasks.ml_tasks import retrain_model_if_needed_task
    drift_alert = {
        "primer_empleo": {"status": "ok"},
        "experiencia": {"status": "ok"},
        "oficio": {"status": "alert"},
        "all": {"status": "ok"},
    }
    retrain_result = {"deployed": True, "metrics": {"f1": 0.82}}
    with patch("app.ml.matching_engine.drift_detector.check_all_types_drift", return_value=drift_alert), \
         patch("asyncio.run", return_value=retrain_result):
        result = retrain_model_if_needed_task.run(worker_type="all")
    assert result is not None


def test_retrain_if_needed_no_reference_triggers_retrain():
    from app.tasks.ml_tasks import retrain_model_if_needed_task
    drift_no_ref = {"all": {"status": "no_reference"}}
    retrain_result = {"deployed": False, "metrics": {}}
    with patch("app.ml.matching_engine.drift_detector.check_all_types_drift", return_value=drift_no_ref), \
         patch("asyncio.run", return_value=retrain_result):
        result = retrain_model_if_needed_task.run(worker_type="all")
    assert result is not None


def test_retrain_if_needed_exception_retries():
    from app.tasks.ml_tasks import retrain_model_if_needed_task
    with patch("app.ml.matching_engine.drift_detector.check_all_types_drift", side_effect=Exception("drift_err")), \
         patch.object(retrain_model_if_needed_task, "retry", side_effect=RuntimeError("retry_raised")), \
         pytest.raises(RuntimeError, match="retry_raised"):
        retrain_model_if_needed_task.run(worker_type="all")


# ── process_alerts_for_new_offer (job_alerts.py lines 78-119) ────────────────

@pytest.mark.asyncio
async def test_process_alerts_no_matching_alerts():
    from app.services.matching.job_alerts import process_alerts_for_new_offer

    offer = MagicMock()
    offer.title = "Trabajo de limpieza"
    offer.district = "Huancayo"
    offer.trade_category = "Limpieza"
    offer.id = uuid.uuid4()

    alert = MagicMock()
    alert.keywords = ["python"]
    alert.districts = []
    alert.trade_categories = []
    alert.salary_min = None

    scalars_res = MagicMock()
    scalars_res.scalars.return_value.all.return_value = [alert]

    db = AsyncMock()
    db.execute.return_value = scalars_res
    redis = AsyncMock()

    # No matching alert → no notification published
    await process_alerts_for_new_offer(offer, db, redis)
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_process_alerts_matching_alert_publishes_notification():
    from app.services.matching.job_alerts import process_alerts_for_new_offer

    offer = MagicMock()
    offer.title = "Instalacion electrica"
    offer.district = "Huancayo"
    offer.trade_category = "Electricidad"
    offer.id = uuid.uuid4()

    alert = MagicMock()
    alert.worker_id = str(uuid.uuid4())
    alert.worker_type = "oficio"
    alert.keywords = []
    alert.districts = []
    alert.trade_categories = ["Electricidad"]
    alert.salary_min = None

    worker = MagicMock()
    worker.user_id = str(uuid.uuid4())

    alerts_res = MagicMock()
    alerts_res.scalars.return_value.all.return_value = [alert]

    worker_res = MagicMock()
    worker_res.scalar_one_or_none.return_value = worker

    db = AsyncMock()
    db.execute.side_effect = [alerts_res, worker_res]
    redis = AsyncMock()

    with patch("app.api.v1.ws_notifications.publish_notification", new=AsyncMock()):
        await process_alerts_for_new_offer(offer, db, redis)

    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_process_alerts_worker_not_found_skips():
    from app.services.matching.job_alerts import process_alerts_for_new_offer

    offer = MagicMock()
    offer.title = "Trabajo"
    offer.district = "Chilca"
    offer.trade_category = "Gasfiteria"
    offer.id = uuid.uuid4()

    alert = MagicMock()
    alert.worker_id = str(uuid.uuid4())
    alert.keywords = []
    alert.districts = []
    alert.trade_categories = ["Gasfiteria"]
    alert.salary_min = None

    alerts_res = MagicMock()
    alerts_res.scalars.return_value.all.return_value = [alert]

    worker_res = MagicMock()
    worker_res.scalar_one_or_none.return_value = None  # worker no existe

    db = AsyncMock()
    db.execute.side_effect = [alerts_res, worker_res]
    redis = AsyncMock()

    await process_alerts_for_new_offer(offer, db, redis)
    # No debe agregar notification si el worker no existe
    db.add.assert_not_called()
    db.commit.assert_called_once()
