# RF: RF001-RF012, RNF001-RNF006
"""Integration tests for the /api/v1/auth endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


def _unique_email(prefix: str = "user") -> str:
    """Generate a unique email to avoid cross-test contamination."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


# ── helpers ──────────────────────────────────────────────────────────────────

async def _register(client: AsyncClient, email: str, password: str = "TestPass1!", role: str = "worker"):
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role},
    )


async def _login(client: AsyncClient, email: str, password: str = "TestPass1!"):
    return await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


# ── register ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_returns_tokens(client: AsyncClient) -> None:
    resp = await _register(client, _unique_email("reg"))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    email = _unique_email("dup")
    r1 = await _register(client, email)
    assert r1.status_code == 200
    r2 = await _register(client, email)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_email_returns_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "TestPass1!"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password_returns_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": _unique_email("short"), "password": "short"},
    )
    assert resp.status_code == 422


# ── login ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_valid_credentials_returns_tokens(client: AsyncClient) -> None:
    email = _unique_email("login")
    await _register(client, email)
    resp = await _login(client, email)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    email = _unique_email("wrongpwd")
    await _register(client, email)
    resp = await _login(client, email, password="WrongPass1!")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email_returns_401(client: AsyncClient) -> None:
    resp = await _login(client, _unique_email("ghost"))
    assert resp.status_code == 401


# ── refresh ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_returns_new_tokens(client: AsyncClient) -> None:
    email = _unique_email("refresh")
    reg = await _register(client, email)
    refresh_token = reg.json()["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_with_access_token_returns_401(client: AsyncClient) -> None:
    email = _unique_email("refreshbad")
    reg = await _register(client, email)
    access_token = reg.json()["access_token"]  # wrong token type

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert resp.status_code == 401


# ── logout ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_logout_returns_200(client: AsyncClient) -> None:
    email = _unique_email("logout")
    reg = await _register(client, email)
    access_token = reg.json()["access_token"]

    resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200, resp.text
    assert "cerrada" in resp.json()["message"].lower()


# ── protected endpoint without token ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_protected_endpoint_without_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/workers/me")
    # HTTPBearer returns 403 when no credentials provided
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["sprint"] == 3
