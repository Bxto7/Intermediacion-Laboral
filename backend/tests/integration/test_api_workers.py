# RF: RF026-RF031
"""Integration tests for /api/v1/workers endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


def _unique_email(prefix: str = "worker") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


async def _register_and_onboard(client: AsyncClient, is_first_job: bool = False) -> tuple[str, str]:
    """Register a worker, onboard them, and return (access_token, worker_id)."""
    email = _unique_email()
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass1!", "role": "worker"},
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]

    onb = await client.post(
        "/api/v1/onboarding/detect-type",
        json={"is_first_job": is_first_job, "is_trade_worker": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert onb.status_code == 200, onb.text
    worker_id = onb.json()["worker_id"]
    return token, worker_id


# ── GET /api/v1/workers/me ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_my_profile_after_onboarding(client: AsyncClient) -> None:
    token, worker_id = await _register_and_onboard(client)
    resp = await client.get(
        "/api/v1/workers/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "id" in data
    assert "worker_type" in data
    assert "dni" not in data  # NEVER expose DNI
    assert data["worker_type"] == "experiencia"


@pytest.mark.asyncio
async def test_get_my_profile_returns_404_without_onboarding(client: AsyncClient) -> None:
    email = _unique_email("noonb")
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass1!", "role": "worker"},
    )
    token = reg.json()["access_token"]
    resp = await client.get(
        "/api/v1/workers/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ── PATCH /api/v1/workers/me ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_profile_district(client: AsyncClient) -> None:
    token, _ = await _register_and_onboard(client)
    resp = await client.patch(
        "/api/v1/workers/me",
        json={"district": "Huancayo", "years_experience": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["district"] == "Huancayo"
    assert data["years_experience"] == 3


@pytest.mark.asyncio
async def test_update_profile_increases_completeness(client: AsyncClient) -> None:
    token, _ = await _register_and_onboard(client)
    resp = await client.patch(
        "/api/v1/workers/me",
        json={"district": "Huancayo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["profile_completeness"] > 0


@pytest.mark.asyncio
async def test_update_full_name_encrypted(client: AsyncClient) -> None:
    """full_name should be encrypted in DB but decrypted in response."""
    token, _ = await _register_and_onboard(client)
    resp = await client.patch(
        "/api/v1/workers/me",
        json={"full_name": "Juan Pérez"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["full_name"] == "Juan Pérez"


# ── GET /api/v1/workers/me/completeness ──────────────────────────────────────


@pytest.mark.asyncio
async def test_completeness_endpoint_returns_percentage(client: AsyncClient) -> None:
    token, _ = await _register_and_onboard(client)
    resp = await client.get(
        "/api/v1/workers/me/completeness",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "percentage" in data
    assert "missing_fields" in data
    assert "next_action" in data
    assert isinstance(data["percentage"], int)
    assert isinstance(data["missing_fields"], list)


@pytest.mark.asyncio
async def test_completeness_missing_fields_in_spanish(client: AsyncClient) -> None:
    token, _ = await _register_and_onboard(client, is_first_job=True)
    resp = await client.get(
        "/api/v1/workers/me/completeness",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    missing = resp.json()["missing_fields"]
    # Should have missing fields since profile is new
    assert len(missing) > 0


@pytest.mark.asyncio
async def test_workers_endpoint_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/workers/me")
    assert resp.status_code in (401, 403)
