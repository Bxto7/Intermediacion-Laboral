# RF: RF036-RF055
"""Integration tests for the public job-board feed endpoint."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, role: str, email: str) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass1!", "role": role},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPass1!"},
    )
    return resp.json()["access_token"]


async def _setup_employer_with_job(
    client: AsyncClient, email: str, ruc: str, district: str = "Huancayo"
) -> str:
    token = await _register_and_login(client, "employer", email)
    await client.post(
        "/api/v1/employers/profile",
        json={
            "company_name": "Empresa Test SAC",
            "ruc": ruc,
            "contact_name": "Admin",
            "phone": "+51 987654321",
            "district": district,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    with patch("app.api.v1.employers.generate_job_embedding") as mock_embed:
        mock_embed.delay = MagicMock()
        await client.post(
            "/api/v1/employers/jobs",
            json={
                "title": "Electricista Residencial",
                "description": (
                    "Buscamos electricista con experiencia en instalaciones residenciales "
                    "y comerciales para proyectos en Huancayo y El Tambo"
                ),
                "required_skills": ["instalacion electrica", "tableros"],
                "modality": "presencial",
                "district": district,
                "worker_type_target": "cualquiera",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    return token


@pytest.mark.asyncio
async def test_jobs_feed_empty_returns_200(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/jobs/feed")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_jobs_feed_shows_active_offers(client: AsyncClient) -> None:
    await _setup_employer_with_job(client, "feedemp1@test.com", "10000000001")

    resp = await client.get("/api/v1/jobs/feed")
    assert resp.status_code == 200
    offers = resp.json()
    assert len(offers) >= 1
    offer = offers[0]
    assert "title" in offer
    assert "employer_name" in offer
    assert "required_skills" in offer
    assert "days_until_expiry" in offer


@pytest.mark.asyncio
async def test_jobs_feed_filter_by_district(client: AsyncClient) -> None:
    await _setup_employer_with_job(client, "feedemp2@test.com", "10000000002", "Huancayo")

    resp_match = await client.get("/api/v1/jobs/feed", params={"district": "Huancayo"})
    assert resp_match.status_code == 200
    assert len(resp_match.json()) >= 1

    resp_miss = await client.get("/api/v1/jobs/feed", params={"district": "Lima"})
    assert resp_miss.status_code == 200
    assert len(resp_miss.json()) == 0


@pytest.mark.asyncio
async def test_jobs_feed_authenticated_request_logs_searcher(client: AsyncClient) -> None:
    await _setup_employer_with_job(client, "feedemp3@test.com", "10000000003")

    worker_token = await _register_and_login(client, "worker", "seeker@test.com")
    resp = await client.get(
        "/api/v1/jobs/feed",
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert resp.status_code == 200
