# RF: RF096-RF110
"""Tests for CV generation helpers and PDF generator."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.nlp.portfolio_nlp.trade_extractor import build_trade_profile_text
from app.nlp.skill_extractor.first_job_extractor import build_first_job_profile_text

# ── Profile text builders ───────────────────────────────────────────────────────

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


# ── Notification tasks ───────────────────────────────────────────────────────────

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


# ── PDF generator template files ────────────────────────────────────────────────

def test_cv_template_files_exist():
    """Verificar que los 3 templates HTML existen."""
    from app.services.cv_builder.pdf_generator import TEMPLATE_MAP, TEMPLATES_DIR

    for worker_type, filename in TEMPLATE_MAP.items():
        template_path = TEMPLATES_DIR / filename
        assert template_path.exists(), f"Template faltante: {template_path}"
        content = template_path.read_text(encoding="utf-8")
        assert "{{ full_name }}" in content, f"Template {filename} no tiene full_name"
        assert len(content) > 100


def test_cv_template_map_has_all_types():
    """TEMPLATE_MAP debe tener los 3 tipos de trabajador."""
    from app.services.cv_builder.pdf_generator import TEMPLATE_MAP
    assert "primer_empleo" in TEMPLATE_MAP
    assert "oficio" in TEMPLATE_MAP
    assert "experiencia" in TEMPLATE_MAP


@pytest.mark.asyncio
async def test_generate_cv_primer_empleo_returns_bytes():
    """CV de PRIMER_EMPLEO debe retornar bytes > 0."""
    from app.services.cv_builder.pdf_generator import generate_cv_pdf

    worker_id = str(uuid4())
    user_id = str(uuid4())

    worker = MagicMock()
    worker.id = worker_id
    worker.worker_type = "primer_empleo"
    worker.district = "Huancayo"
    worker.user_id = user_id
    worker.full_name = b"encrypted_name"
    worker.phone = b"encrypted_phone"

    user_mock = MagicMock()
    user_mock.email = "test@example.com"

    wizard = MagicMock()
    wizard.extracted_skills = ["responsabilidad", "puntualidad"]
    wizard.answers = {"education": [], "activities": [], "job_interests": "comercio", "linkedin": ""}

    worker_result = MagicMock()
    worker_result.scalar_one_or_none.return_value = worker

    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user_mock

    wizard_result = MagicMock()
    wizard_result.scalar_one_or_none.return_value = wizard

    db = AsyncMock()
    db.execute.side_effect = [worker_result, user_result, wizard_result]

    with patch("app.services.cv_builder.pdf_generator.decrypt_field", return_value="Test User"):
        result = await generate_cv_pdf(worker_id, db)

    assert isinstance(result, bytes)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_cv_worker_not_found_raises():
    """Worker inexistente debe lanzar ValueError."""
    from app.services.cv_builder.pdf_generator import generate_cv_pdf

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = mock_result

    with pytest.raises(ValueError, match="no encontrado"):
        await generate_cv_pdf(str(uuid4()), db)


# ── Equity ranker ─────────────────────────────────────────────────────────────────

def test_equity_ranker_stable_when_one_group():
    """Con un solo grupo no debe modificar scores."""
    from app.ml.equity_ranker.ranker import apply_equity_reranking

    matches = [
        {"combined_score": 0.9, "district": "Huancayo"},
        {"combined_score": 0.7, "district": "Huancayo"},
    ]
    result = apply_equity_reranking(matches)
    assert len(result) == 2
    assert result[0]["combined_score"] >= result[1]["combined_score"]


def test_equity_ranker_empty_input():
    """Lista vacia no debe lanzar error."""
    from app.ml.equity_ranker.ranker import apply_equity_reranking
    assert apply_equity_reranking([]) == []


def test_disparate_impact_calculation():
    """Calculo correcto del ratio entre grupos."""
    from app.ml.equity_ranker.ranker import compute_disparate_impact
    ratio = compute_disparate_impact([0.8, 0.9], [0.4, 0.5])
    assert ratio == pytest.approx(0.85 / 0.45, abs=0.01)


def test_disparate_impact_empty_groups():
    """Grupos vacios retornan 1.0 (sin disparidad)."""
    from app.ml.equity_ranker.ranker import compute_disparate_impact
    assert compute_disparate_impact([], [0.5]) == 1.0
    assert compute_disparate_impact([0.5], []) == 1.0


def test_equity_log_audit():
    """log_equity_audit no debe lanzar error."""
    from app.ml.equity_ranker.ranker import log_equity_audit
    log_equity_audit("worker-1", "oficio", 0.75, True)
    log_equity_audit("worker-2", "experiencia", 0.90, False)


# ── Explainer ───────────────────────────────────────────────────────────────────

def test_explainer_alta_label():
    from app.ml.explainer.explainer import explain_match
    result = explain_match(
        combined_score=0.85,
        worker_skills=["python", "fastapi", "sql"],
        offer_required_skills=["python", "sql"],
        offer_preferred_skills=["fastapi"],
        worker_type="experiencia",
    )
    assert result["compatibility_label"] == "Alta"
    assert "message" in result
    assert 0 <= result["combined_score"] <= 1.0


def test_explainer_media_label():
    from app.ml.explainer.explainer import explain_match
    result = explain_match(
        combined_score=0.55,
        worker_skills=["carpinteria"],
        offer_required_skills=["carpinteria", "pintura"],
        offer_preferred_skills=[],
        worker_type="oficio",
    )
    assert result["compatibility_label"] == "Media"


def test_explainer_baja_label():
    from app.ml.explainer.explainer import explain_match
    result = explain_match(
        combined_score=0.2,
        worker_skills=["carpinteria"],
        offer_required_skills=["python", "java", "kubernetes"],
        offer_preferred_skills=[],
        worker_type="primer_empleo",
    )
    assert result["compatibility_label"] == "Baja"
    assert len(result["missing_skills"]) > 0


# ── Schemas ─────────────────────────────────────────────────────────────────────

def test_matching_schemas_importable():
    """Los schemas de matching deben importarse sin error."""
    from app.schemas.matching import JobMatchResult, MatchExplanation, MatchResponse
    assert MatchExplanation is not None
    assert JobMatchResult is not None
    assert MatchResponse is not None


# ── CV template context — oficio and experiencia branches ────────────────────────

@pytest.mark.asyncio
async def test_build_template_context_oficio():
    """_build_template_context para oficio devuelve trade_category y portfolio_entries."""
    from app.services.cv_builder.pdf_generator import _build_template_context

    worker_id = str(uuid4())
    user_id = str(uuid4())

    worker = MagicMock()
    worker.id = worker_id
    worker.user_id = user_id
    worker.worker_type = "oficio"
    worker.full_name = b"encrypted"
    worker.phone = None
    worker.district = "El Tambo"
    worker.trade_category = "Electricidad"
    worker.years_experience = 4
    worker.avg_rating = 4.5

    user_mock = MagicMock()
    user_mock.email = "oficio@test.com"

    entry = MagicMock()
    entry.title = "Instalacion residencial"
    entry.description = "Cableado completo"
    entry.extracted_skills = ["cableado", "tableros"]
    entry.period_start = None
    entry.client_rating = 4.8

    user_res = MagicMock()
    user_res.scalar_one_or_none.return_value = user_mock

    entries_res = MagicMock()
    entries_res.scalars.return_value.all.return_value = [entry]

    db = AsyncMock()
    db.execute.side_effect = [user_res, entries_res]

    with patch("app.services.cv_builder.pdf_generator.decrypt_field", return_value="Nombre Oficio"):
        ctx = await _build_template_context(worker, "oficio", db)

    assert ctx["trade_category"] == "Electricidad"
    assert ctx["portfolio_count"] == 1
    assert "cableado" in ctx["skills"] or "tableros" in ctx["skills"]


@pytest.mark.asyncio
async def test_build_template_context_experiencia():
    """_build_template_context para experiencia devuelve job_title y years_experience."""
    from app.services.cv_builder.pdf_generator import _build_template_context

    worker_id = str(uuid4())
    user_id = str(uuid4())

    worker = MagicMock()
    worker.id = worker_id
    worker.user_id = user_id
    worker.worker_type = "experiencia"
    worker.full_name = b"encrypted_exp"
    worker.phone = b"encrypted_phone"
    worker.district = "Huancayo"
    worker.bio = "Contador con experiencia"
    worker.job_title = "Contador CPA"
    worker.years_experience = 8
    worker.avg_rating = 0

    user_mock = MagicMock()
    user_mock.email = "exp@test.com"

    user_res = MagicMock()
    user_res.scalar_one_or_none.return_value = user_mock

    db = AsyncMock()
    db.execute.return_value = user_res

    with patch("app.services.cv_builder.pdf_generator.decrypt_field", return_value="Nombre Exp"):
        ctx = await _build_template_context(worker, "experiencia", db)

    assert ctx["job_title"] == "Contador CPA"
    assert ctx["years_experience"] == 8
    assert ctx["email"] == "exp@test.com"


# ── Job alerts unit tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_job_alerts_returns_list():
    """list_job_alerts retorna lista de alertas del worker."""
    from app.services.matching.job_alerts import list_job_alerts

    alert1 = MagicMock()
    alert1.keywords = ["python"]

    scalars_mock = MagicMock()
    scalars_mock.scalars.return_value.all.return_value = [alert1]

    db = AsyncMock()
    db.execute.return_value = scalars_mock

    result = await list_job_alerts("worker-123", db)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_deactivate_job_alert_found():
    """deactivate_job_alert retorna True cuando la alerta existe."""
    from app.services.matching.job_alerts import deactivate_job_alert

    alert = MagicMock()
    alert.is_active = True

    res = MagicMock()
    res.scalar_one_or_none.return_value = alert

    db = AsyncMock()
    db.execute.return_value = res

    result = await deactivate_job_alert("alert-1", "worker-1", db)
    assert result is True
    assert alert.is_active is False


@pytest.mark.asyncio
async def test_deactivate_job_alert_not_found():
    """deactivate_job_alert retorna False cuando la alerta no existe."""
    from app.services.matching.job_alerts import deactivate_job_alert

    res = MagicMock()
    res.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = res

    result = await deactivate_job_alert("nonexistent", "worker-1", db)
    assert result is False


def test_alert_matches_offer_trade_category_filter():
    """No debe coincidir si trade_category no esta en la lista de la alerta."""
    from app.services.matching.job_alerts import _alert_matches_offer

    alert = MagicMock()
    alert.keywords = []
    alert.districts = []
    alert.trade_categories = ["Electricidad"]
    alert.salary_min = None

    offer = MagicMock()
    offer.title = "Trabajo de gasfiteria"
    offer.description = ""
    offer.district = None
    offer.trade_category = "Gasfiteria"

    assert _alert_matches_offer(alert, offer) is False


def test_alert_matches_offer_salary_filter():
    """No debe coincidir si el salario de la oferta es menor al minimo de la alerta."""
    from app.services.matching.job_alerts import _alert_matches_offer

    alert = MagicMock()
    alert.keywords = []
    alert.districts = []
    alert.trade_categories = []
    alert.salary_min = 2000.0

    offer = MagicMock()
    offer.title = "Trabajo cualquiera"
    offer.description = ""
    offer.district = None
    offer.trade_category = None
    offer.salary_min = 1500.0

    assert _alert_matches_offer(alert, offer) is False


def test_alert_matches_offer_salary_ok():
    """Debe coincidir si el salario supera el minimo."""
    from app.services.matching.job_alerts import _alert_matches_offer

    alert = MagicMock()
    alert.keywords = []
    alert.districts = []
    alert.trade_categories = []
    alert.salary_min = 1000.0

    offer = MagicMock()
    offer.title = "Oferta con buen salario"
    offer.description = ""
    offer.district = None
    offer.trade_category = None
    offer.salary_min = 2500.0

    assert _alert_matches_offer(alert, offer) is True


# ── Additional branch coverage ───────────────────────────────────────────────────

def test_compute_disparate_impact_zero_mean_b():
    """Retorna 1.0 cuando el promedio del grupo B es 0."""
    from app.ml.equity_ranker.ranker import compute_disparate_impact
    result = compute_disparate_impact([0.8, 0.9], [0.0, 0.0])
    assert result == 1.0


@pytest.mark.asyncio
async def test_resolve_cold_start_exception_path():
    """Excepcion en generate_embedding_sync es capturada y logueada."""
    from app.ml.cold_start.resolver import resolve_cold_start

    worker = MagicMock()
    worker.id = "worker-exc"
    worker.worker_type = "experiencia"
    worker.bio = "bio"
    worker.job_title = "titulo"
    worker.years_experience = 1
    worker.district = "Huancayo"
    worker.embedding = None

    db = AsyncMock()

    with patch("app.ml.cold_start.resolver.generate_embedding_sync", side_effect=RuntimeError("model error")):
        result = await resolve_cold_start(worker, db)

    assert result is worker


@pytest.mark.asyncio
async def test_create_job_alert_worker_not_found():
    """ValueError cuando el worker no existe en BD."""
    from app.services.matching.job_alerts import create_job_alert

    res = MagicMock()
    res.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = res

    with pytest.raises(ValueError, match="no encontrado"):
        await create_job_alert("missing-worker", [], [], [], None, db)


def test_alert_matches_offer_keywords_no_match():
    """Retorna False cuando los keywords no aparecen en el texto de la oferta."""
    from app.services.matching.job_alerts import _alert_matches_offer

    alert = MagicMock()
    alert.keywords = ["python", "django"]
    alert.districts = []
    alert.trade_categories = []
    alert.salary_min = None

    offer = MagicMock()
    offer.title = "Trabajo de gasfiteria residencial"
    offer.description = "Instalacion de tuberias"
    offer.district = None

    assert _alert_matches_offer(alert, offer) is False


@pytest.mark.asyncio
async def test_build_template_context_phone_decryption_failure():
    """Excepcion en decrypt_field para phone resulta en string vacio."""
    from app.services.cv_builder.pdf_generator import _build_template_context

    worker = MagicMock()
    worker.id = str(uuid4())
    worker.user_id = str(uuid4())
    worker.worker_type = "primer_empleo"
    worker.full_name = b"encrypted_name"
    worker.phone = b"corrupted_phone_data"
    worker.district = "Huancayo"
    worker.avg_rating = 0

    user_mock = MagicMock()
    user_mock.email = "test@test.com"

    user_res = MagicMock()
    user_res.scalar_one_or_none.return_value = user_mock

    wizard_res = MagicMock()
    wizard_res.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.side_effect = [user_res, wizard_res]

    def mock_decrypt(val):
        if val == b"corrupted_phone_data":
            raise ValueError("bad data")
        return "Nombre Test"

    with patch("app.services.cv_builder.pdf_generator.decrypt_field", side_effect=mock_decrypt):
        ctx = await _build_template_context(worker, "primer_empleo", db)

    assert ctx["phone"] == ""
    assert ctx["full_name"] == "Nombre Test"


# ── File validator ───────────────────────────────────────────────────────────────

def test_file_validator_constants():
    """Verificar constantes del validador de archivos."""
    from app.utils.file_validator import ALLOWED_MIME_TYPES, MAX_FILE_SIZE_BYTES
    assert "image/jpeg" in ALLOWED_MIME_TYPES
    assert "image/png" in ALLOWED_MIME_TYPES
    assert "image/webp" in ALLOWED_MIME_TYPES
    assert MAX_FILE_SIZE_BYTES == 5 * 1024 * 1024
