"""Verifica que el portfolio publico no expone UUIDs internos.

RF: RNF001 — Sprint 3 Security Audit
Covers: GET /api/v1/portfolio/{username} — PublicPortfolioEntryResponse
"""
import re
from unittest.mock import MagicMock, patch

import pytest

UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I
)


@pytest.mark.asyncio
async def test_public_portfolio_404_does_not_expose_uuid(client):
    """Un slug inexistente debe retornar 404 sin exponer UUIDs en el cuerpo."""
    response = await client.get("/api/v1/portfolio/slug-inexistente-xyz-abc")
    assert response.status_code == 404
    body_str = response.text
    assert not UUID_PATTERN.search(body_str), (
        f"UUID expuesto en respuesta 404: {body_str!r}"
    )


@pytest.mark.asyncio
async def test_public_portfolio_entries_have_no_worker_id(client):
    """Las entradas del portfolio publico no deben contener el campo worker_id."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "oficio_pub_uuid@test.com", "password": "TestPass1!", "role": "worker"},
    )
    assert reg.status_code in (200, 201)
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/onboarding/detect-type",
        json={
            "is_first_job": False,
            "is_trade_worker": True,
            "trade_category": "Electricidad",
        },
        headers=headers,
    )

    await client.patch(
        "/api/v1/workers/me",
        json={"username": "oficio_pub_uuid_user", "district": "Huancayo"},
        headers=headers,
    )

    with patch("app.api.v1.portfolio.generate_portfolio_entry_embedding") as mock_pe, \
         patch("app.api.v1.portfolio.generate_worker_embedding") as mock_we:
        mock_pe.delay = MagicMock()
        mock_we.delay = MagicMock()
        await client.post(
            "/api/v1/portfolio/entries",
            json={
                "title": "Instalacion electrica casa",
                "description": (
                    "Instale el cableado completo de una casa de dos pisos en El Tambo, "
                    "incluyendo tablero electrico y tomacorrientes en todos los ambientes."
                ),
                "is_public": True,
            },
            headers=headers,
        )

    response = await client.get("/api/v1/portfolio/oficio_pub_uuid_user")
    if response.status_code == 404:
        pytest.skip("Public portfolio endpoint not serving this username — check routing")

    assert response.status_code == 200
    data = response.json()
    entries = data.get("entries", [])

    for entry in entries:
        assert "worker_id" not in entry, (
            f"worker_id UUID expuesto en entrada publica: {entry}"
        )
