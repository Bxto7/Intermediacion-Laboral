# RF: RF111-RF117 (M07) — alertas configurables de empleo
"""Integration tests for job alerts endpoints."""
import pytest
from httpx import AsyncClient


async def _register_worker(client: AsyncClient, email: str) -> dict:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass1!", "role": "worker"},
    )
    assert reg.status_code in (200, 201)
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/onboarding/detect-type",
        json={"is_first_job": False, "is_trade_worker": False},
        headers=headers,
    )
    return {"token": token, "headers": headers}


@pytest.mark.asyncio
async def test_create_job_alert_requires_auth(client: AsyncClient):
    """Sin token → 401/403."""
    resp = await client.post("/api/v1/alerts", json={"keywords": ["python"]})
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_job_alert_success(client: AsyncClient):
    """Trabajador autenticado puede crear una alerta."""
    import uuid
    data = await _register_worker(client, f"alert_test_{uuid.uuid4().hex[:6]}@test.com")
    headers = data["headers"]

    resp = await client.post(
        "/api/v1/alerts",
        json={
            "keywords": ["electricista", "instalacion"],
            "districts": ["Huancayo"],
            "trade_categories": [],
            "salary_min": None,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["is_active"] is True
    assert "electricista" in body["keywords"]
    assert "Huancayo" in body["districts"]


@pytest.mark.asyncio
async def test_list_job_alerts(client: AsyncClient):
    """Lista retorna las alertas del trabajador."""
    import uuid
    data = await _register_worker(client, f"alert_list_{uuid.uuid4().hex[:6]}@test.com")
    headers = data["headers"]

    # Crear 2 alertas
    await client.post(
        "/api/v1/alerts",
        json={"keywords": ["programador"], "districts": [], "trade_categories": []},
        headers=headers,
    )
    await client.post(
        "/api/v1/alerts",
        json={"keywords": ["tecnico"], "districts": ["El Tambo"], "trade_categories": []},
        headers=headers,
    )

    resp = await client.get("/api/v1/alerts", headers=headers)
    assert resp.status_code == 200
    alerts = resp.json()
    assert len(alerts) >= 2


@pytest.mark.asyncio
async def test_delete_nonexistent_alert_returns_404(client: AsyncClient):
    """Eliminar alerta inexistente → 404."""
    import uuid
    data = await _register_worker(client, f"alert_del_{uuid.uuid4().hex[:6]}@test.com")
    headers = data["headers"]

    resp = await client.delete(f"/api/v1/alerts/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_alert_matches_offer_keywords():
    """_alert_matches_offer debe retornar True cuando keywords coinciden."""
    from unittest.mock import MagicMock

    from app.services.matching.job_alerts import _alert_matches_offer

    alert = MagicMock()
    alert.keywords = ["electricista"]
    alert.districts = []
    alert.trade_categories = []
    alert.salary_min = None

    offer = MagicMock()
    offer.title = "Se busca electricista para proyecto"
    offer.description = "Instalacion residencial"
    offer.district = "Huancayo"

    assert _alert_matches_offer(alert, offer) is True


@pytest.mark.asyncio
async def test_alert_no_match_wrong_district():
    """Oferta en otro distrito no debe coincidir."""
    from unittest.mock import MagicMock

    from app.services.matching.job_alerts import _alert_matches_offer

    alert = MagicMock()
    alert.keywords = []
    alert.districts = ["El Tambo"]
    alert.trade_categories = []
    alert.salary_min = None

    offer = MagicMock()
    offer.title = "Trabajo cualquiera"
    offer.description = "Descripcion"
    offer.district = "Huancayo"

    assert _alert_matches_offer(alert, offer) is False
