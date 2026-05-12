# RF: RF136-RF145 (M09) — Tests de integración del panel admin DRTPE
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.fixture
def admin_token(client):
    """Token JWT con rol ADMIN para tests."""
    from app.core.security import create_access_token
    return create_access_token({"sub": str(uuid4()), "role": "admin"})


@pytest.fixture
def worker_token(client):
    """Token JWT con rol WORKER para tests de autorización."""
    from app.core.security import create_access_token
    return create_access_token({"sub": str(uuid4()), "role": "worker"})


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client: AsyncClient):
    """GET /admin/dashboard sin token → 401."""
    response = await client.get("/api/v1/admin/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_blocks_worker_role(client: AsyncClient, worker_token: str):
    """GET /admin/dashboard con token WORKER → 403."""
    with patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock, return_value=False):
        response = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_returns_kpis_for_admin(client: AsyncClient, admin_token: str):
    """GET /admin/dashboard con token ADMIN → 200 con los 7 KPIs."""
    mock_kpis = {
        "vil": {},
        "ivp": {},
        "tf": {},
        "rbs": {"avg_pct": 0.0, "n_pairs": 0},
        "tcc": {},
        "ivm": {"ivm_pct": 0.0, "total_oficio": 0},
        "tcss": {},
        "calculated_at": "2026-05-06T00:00:00+00:00",
    }
    with (
        patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock, return_value=False),
        patch(
            "app.api.v1.admin.dashboard.calculate_all_kpis",
            new_callable=AsyncMock,
            return_value=mock_kpis,
        ),
        patch("app.api.v1.admin.dashboard.get_redis") as mock_redis_factory,
    ):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.setex = AsyncMock()
        mock_redis_factory.return_value = redis_mock

        response = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 200
    body = response.json()
    for kpi_key in ["vil", "ivp", "tf", "rbs", "tcc", "ivm", "tcss"]:
        assert kpi_key in body, f"KPI '{kpi_key}' debe estar en la respuesta"
    assert "calculated_at" in body


@pytest.mark.asyncio
async def test_model_metrics_requires_admin(client: AsyncClient, worker_token: str):
    """GET /admin/model/metrics sin token ADMIN → 403."""
    with patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock, return_value=False):
        response = await client.get(
            "/api/v1/admin/model/metrics",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_model_metrics_404_when_no_model(client: AsyncClient, admin_token: str):
    """GET /admin/model/metrics cuando no hay modelo → 404."""
    with (
        patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock, return_value=False),
        patch(
            "app.api.v1.admin.dashboard.load_model_metrics",
            side_effect=FileNotFoundError,
        ),
    ):
        response = await client.get(
            "/api/v1/admin/model/metrics",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_worker_stats_requires_admin(client: AsyncClient, worker_token: str):
    """GET /admin/workers/stats sin token ADMIN → 403."""
    with patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock, return_value=False):
        response = await client.get(
            "/api/v1/admin/workers/stats",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_uses_redis_cache(client: AsyncClient, admin_token: str):
    """Si hay cache en Redis, no debe recalcular los KPIs."""
    import json

    cached = {
        "vil": {}, "ivp": {}, "tf": {}, "rbs": {"avg_pct": 5.0, "n_pairs": 3},
        "tcc": {}, "ivm": {"ivm_pct": 60.0, "total_oficio": 10}, "tcss": {},
        "calculated_at": "2026-05-06T00:00:00+00:00",
    }
    with (
        patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock, return_value=False),
        patch("app.api.v1.admin.dashboard.get_redis") as mock_redis_factory,
        patch("app.api.v1.admin.dashboard.calculate_all_kpis") as mock_calc,
    ):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=json.dumps(cached).encode())
        mock_redis_factory.return_value = redis_mock

        response = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 200
    mock_calc.assert_not_called()
    assert response.json()["rbs"]["avg_pct"] == 5.0
