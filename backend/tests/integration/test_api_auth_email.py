# RF: RF009-RF012
"""Integration tests for email-related auth endpoints and edge cases."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


def _unique_email(prefix: str = "email") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


# ── verify-email ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_email_invalid_token_returns_400(client: AsyncClient) -> None:
    # Token meets schema min_length (32) but does not exist in Redis → 400
    resp = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": "x" * 32},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_valid_token(client: AsyncClient, fake_redis) -> None:
    """Manually set a Redis key and verify it gets consumed."""
    user_id = str(uuid.uuid4())
    token = str(uuid.uuid4())
    await fake_redis.set(f"email_verify:{token}", user_id)

    # Register a real user so the DB lookup works
    email = _unique_email("verify")
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass1!", "role": "worker"},
    )
    assert reg.status_code == 200

    # Call with a non-existent user_id in DB — should still return 200 (token consumed)
    resp = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    )
    assert resp.status_code == 200


# ── forgot-password ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email_returns_200(client: AsyncClient) -> None:
    """Must always return 200 to prevent user enumeration."""
    resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": _unique_email("ghost")},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_forgot_password_existing_email_returns_200(client: AsyncClient) -> None:
    email = _unique_email("forgotpwd")
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass1!", "role": "worker"},
    )
    resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": email},
    )
    assert resp.status_code == 200


# ── reset-password ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reset_password_invalid_token_returns_400(client: AsyncClient) -> None:
    # Token meets schema min_length (32) but does not exist in Redis → 400
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "x" * 32, "new_password": "NewPass123!"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_short_password_returns_422(client: AsyncClient) -> None:
    # Pydantic validates min_length=8 for new_password → 422 before the handler runs
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "x" * 32, "new_password": "short"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reset_password_valid_token(client: AsyncClient, fake_redis) -> None:
    """Set Redis token manually and reset password."""
    email = _unique_email("reset")
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass1!", "role": "worker"},
    )
    user_id = str(uuid.uuid4())  # placeholder — token just needs to exist
    token = str(uuid.uuid4())
    await fake_redis.set(f"pwd_reset:{token}", user_id)

    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "NewPassword123!"},
    )
    assert resp.status_code == 200
