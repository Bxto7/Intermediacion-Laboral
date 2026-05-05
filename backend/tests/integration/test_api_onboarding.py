# RF: RF016-RF022
"""Integration tests for /api/v1/onboarding endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


def _unique_email(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


# ── helpers ──────────────────────────────────────────────────────────────────

async def _register_worker(client: AsyncClient) -> str:
    """Register a unique worker user and return its access token."""
    email = _unique_email("worker")
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass1!", "role": "worker"},
    )
    assert reg.status_code == 200, reg.text
    return reg.json()["access_token"]


async def _detect_type(client: AsyncClient, token: str, payload: dict):
    return await client.post(
        "/api/v1/onboarding/detect-type",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )


# ── detect-type ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_onboarding_primer_empleo(client: AsyncClient) -> None:
    token = await _register_worker(client)
    resp = await _detect_type(
        client, token, {"is_first_job": True, "is_trade_worker": False}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["worker_type"] == "primer_empleo"
    assert "worker_id" in data
    assert "next_step" in data


@pytest.mark.asyncio
async def test_onboarding_oficio_con_categoria(client: AsyncClient) -> None:
    token = await _register_worker(client)
    resp = await _detect_type(
        client,
        token,
        {
            "is_first_job": False,
            "is_trade_worker": True,
            "trade_category": "Electricidad",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["worker_type"] == "oficio"


@pytest.mark.asyncio
async def test_onboarding_experiencia(client: AsyncClient) -> None:
    token = await _register_worker(client)
    resp = await _detect_type(
        client, token, {"is_first_job": False, "is_trade_worker": False}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["worker_type"] == "experiencia"


@pytest.mark.asyncio
async def test_onboarding_sin_autenticacion_devuelve_401(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/onboarding/detect-type",
        json={"is_first_job": True, "is_trade_worker": False},
    )
    # HTTPBearer returns 403 when no credentials provided
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_onboarding_duplicado_devuelve_409(client: AsyncClient) -> None:
    token = await _register_worker(client)
    payload = {"is_first_job": True, "is_trade_worker": False}
    r1 = await _detect_type(client, token, payload)
    assert r1.status_code == 200, r1.text
    r2 = await _detect_type(client, token, payload)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_onboarding_oficio_sin_categoria_devuelve_422(client: AsyncClient) -> None:
    token = await _register_worker(client)
    resp = await _detect_type(
        client,
        token,
        {"is_first_job": False, "is_trade_worker": True, "trade_category": None},
    )
    assert resp.status_code == 422


# ── status ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_onboarding_status_antes_de_onboarding(client: AsyncClient) -> None:
    token = await _register_worker(client)
    resp = await client.get(
        "/api/v1/onboarding/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["is_onboarded"] is False
    assert data["worker_type"] is None


@pytest.mark.asyncio
async def test_onboarding_status_despues_de_onboarding(client: AsyncClient) -> None:
    token = await _register_worker(client)
    await _detect_type(client, token, {"is_first_job": True, "is_trade_worker": False})

    resp = await client.get(
        "/api/v1/onboarding/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["is_onboarded"] is True
    assert data["worker_type"] == "primer_empleo"
