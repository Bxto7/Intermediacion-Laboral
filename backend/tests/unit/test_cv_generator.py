# RF: RF106-RF110
"""Tests for CV generation helpers."""

from app.nlp.skill_extractor.first_job_extractor import build_first_job_profile_text
from app.nlp.portfolio_nlp.trade_extractor import build_trade_profile_text


def test_build_first_job_profile_text_contains_district():
    text = build_first_job_profile_text(
        district="Huancayo",
        skills=["puntualidad", "trabajo colaborativo"],
        interests=["comercio", "logistica"],
        education_level="secundaria",
    )
    assert "Huancayo" in text
    assert "primer empleo" in text.lower() or "empleo" in text.lower()


def test_build_first_job_profile_text_includes_skills():
    text = build_first_job_profile_text(
        district="El Tambo",
        skills=["responsabilidad", "comunicacion efectiva"],
        interests=[],
        education_level="tecnica",
    )
    assert "responsabilidad" in text or "comunicacion" in text


def test_build_trade_profile_text_contains_trade_category():
    text = build_trade_profile_text(
        trade_category="Electricidad",
        years_experience=3,
        district="Chilca",
        avg_rating=4.0,
        portfolio_skills=["cableado", "tableros"],
        portfolio_count=5,
    )
    assert "Electricidad" in text
    assert "3" in text
    assert "Chilca" in text
    assert "cableado" in text


def test_send_push_notification_returns_queued():
    from app.tasks.notifications import send_push_notification
    result = send_push_notification("user-abc", "Nuevo mensaje", "Tienes una notificacion")
    assert result == {"status": "queued"}


def test_notify_employer_new_application_returns_queued():
    from app.tasks.notifications import notify_employer_new_application
    result = notify_employer_new_application("emp-1", "job-1", "worker-1")
    assert result == {"status": "queued"}


def test_notify_worker_hired_returns_queued():
    from app.tasks.notifications import notify_worker_hired
    result = notify_worker_hired("worker-2", "job-2")
    assert result == {"status": "queued"}
