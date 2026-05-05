# RF: RF059-RF079
"""Integration tests for NLP endpoints — type enforcement and basic functionality."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient


async def _register_and_onboard(
    client: AsyncClient,
    email: str,
    worker_type: str,
    trade_category: str | None = None,
) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass1!", "role": "worker"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPass1!"},
    )
    token = resp.json()["access_token"]

    if worker_type == "primer_empleo":
        payload: dict = {"is_first_job": True, "is_trade_worker": False}
    elif worker_type == "oficio":
        payload = {
            "is_first_job": False,
            "is_trade_worker": True,
            "trade_category": trade_category or "Electricidad",
        }
    else:
        payload = {"is_first_job": False, "is_trade_worker": False}

    await client.post(
        "/api/v1/onboarding/detect-type",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    return token


@pytest.mark.asyncio
async def test_extract_skills_wizard_requires_primer_empleo_type(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "nlp1@test.com", "experiencia")
    resp = await client.post(
        "/api/v1/nlp/extract-skills/wizard",
        json={"step": 3, "text": "soy puntual y trabajo bien en equipo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_parse_cv_requires_experiencia_type(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "nlp2@test.com", "primer_empleo")
    resp = await client.post(
        "/api/v1/nlp/parse-cv",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4\n%%EOF"), "application/pdf")},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_parse_cv_validates_mime_type(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "nlp3@test.com", "experiencia")
    resp = await client.post(
        "/api/v1/nlp/parse-cv",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("foto.png", io.BytesIO(b"\x89PNG\r\n"), "image/png")},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_extract_portfolio_skills_returns_skills_list(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "nlp4@test.com", "oficio", "Electricidad")
    resp = await client.post(
        "/api/v1/nlp/extract-skills/portfolio",
        json={
            "description": (
                "Instale cableado electrico en una casa de dos pisos en Huancayo, "
                "puse tomacorrientes y el tablero electrico principal"
            ),
            "trade_category": "Electricidad",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "skills" in data
    assert isinstance(data["skills"], list)
    assert "estimated_level" in data


@pytest.mark.asyncio
async def test_extract_skills_wizard_returns_skills(client: AsyncClient) -> None:
    """Spec #2: PRIMER_EMPLEO → skills list returned."""
    token = await _register_and_onboard(client, "nlp5@test.com", "primer_empleo")
    resp = await client.post(
        "/api/v1/nlp/extract-skills/wizard",
        json={"step": 3, "text": "soy puntual y trabajador, me gusta el trabajo en equipo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "skills" in data
    assert isinstance(data["skills"], list)
    assert len(data["skills"]) > 0


@pytest.mark.asyncio
async def test_parse_cv_file_too_large(client: AsyncClient) -> None:
    """Spec #5: file > 10 MB → 422."""
    token = await _register_and_onboard(client, "nlp6@test.com", "experiencia")
    big_content = b"%PDF-1.4\n" + b"x" * (11 * 1024 * 1024)
    resp = await client.post(
        "/api/v1/nlp/parse-cv",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("big_cv.pdf", io.BytesIO(big_content), "application/pdf")},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_extract_portfolio_skills_oficio_only(client: AsyncClient) -> None:
    """Spec #6: EXPERIENCIA trying portfolio NLP → 403."""
    token = await _register_and_onboard(client, "nlp7@test.com", "experiencia")
    resp = await client.post(
        "/api/v1/nlp/extract-skills/portfolio",
        json={
            "description": "Instale cableado electrico en casa",
            "trade_category": "Electricidad",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
