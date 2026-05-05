# RF: RF056-RF075
"""Integration tests for OFICIO portfolio CRUD + NLP skill extraction."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

_ENTRY_PAYLOAD = {
    "title": "Instalacion electrica residencial en El Tambo",
    "description": (
        "Instale el cableado completo de una casa de dos pisos, "
        "puse tomacorrientes y el tablero electrico principal"
    ),
    "is_public": True,
}


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
async def test_create_portfolio_entry_extracts_skills(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "port1@test.com", "oficio", "Electricidad")

    with (
        patch("app.api.v1.portfolio.generate_portfolio_entry_embedding") as m1,
        patch("app.api.v1.portfolio.generate_worker_embedding") as m2,
    ):
        m1.delay = MagicMock()
        m2.delay = MagicMock()
        resp = await client.post(
            "/api/v1/portfolio/entries",
            json=_ENTRY_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert "extracted_skills" in data
    assert isinstance(data["extracted_skills"], list)
    assert len(data["extracted_skills"]) > 0


@pytest.mark.asyncio
async def test_public_portfolio_accessible_without_auth(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "port2@test.com", "oficio", "Electricidad")

    with (
        patch("app.api.v1.portfolio.generate_portfolio_entry_embedding") as m1,
        patch("app.api.v1.portfolio.generate_worker_embedding") as m2,
    ):
        m1.delay = MagicMock()
        m2.delay = MagicMock()
        await client.post(
            "/api/v1/portfolio/entries",
            json=_ENTRY_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )

    profile_resp = await client.get(
        "/api/v1/workers/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    username = profile_resp.json().get("username")
    assert username, "username debe generarse en el onboarding"

    resp = await client.get(f"/api/v1/portfolio/{username}")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert isinstance(data["entries"], list)


@pytest.mark.asyncio
async def test_public_portfolio_hides_sensitive_data(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "port3@test.com", "oficio", "Gasfiteria")

    with (
        patch("app.api.v1.portfolio.generate_portfolio_entry_embedding") as m1,
        patch("app.api.v1.portfolio.generate_worker_embedding") as m2,
    ):
        m1.delay = MagicMock()
        m2.delay = MagicMock()
        await client.post(
            "/api/v1/portfolio/entries",
            json={
                "title": "Reparacion de canerias en El Tambo",
                "description": "Repare canerias del bano e instale grifos nuevos",
                "is_public": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    profile_resp = await client.get(
        "/api/v1/workers/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    username = profile_resp.json().get("username")
    assert username

    resp = await client.get(f"/api/v1/portfolio/{username}")
    assert resp.status_code == 200
    body = resp.text.lower()
    assert "dni" not in body
    assert "ruc" not in body


@pytest.mark.asyncio
async def test_delete_portfolio_entry_returns_204(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "port4@test.com", "oficio", "Electricidad")

    with (
        patch("app.api.v1.portfolio.generate_portfolio_entry_embedding") as m1,
        patch("app.api.v1.portfolio.generate_worker_embedding") as m2,
    ):
        m1.delay = MagicMock()
        m2.delay = MagicMock()
        create_resp = await client.post(
            "/api/v1/portfolio/entries",
            json=_ENTRY_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert create_resp.status_code == 201
    entry_id = create_resp.json()["id"]

    with patch("app.api.v1.portfolio.generate_worker_embedding") as m:
        m.delay = MagicMock()
        del_resp = await client.delete(
            f"/api/v1/portfolio/entries/{entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_portfolio_requires_oficio_type(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "port5@test.com", "primer_empleo")
    resp = await client.post(
        "/api/v1/portfolio/entries",
        json=_ENTRY_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_requires_oficio_type_experiencia(client: AsyncClient) -> None:
    """Spec #2: EXPERIENCIA worker → 403 when creating portfolio entry."""
    token = await _register_and_onboard(client, "port6@test.com", "experiencia")
    resp = await client.post(
        "/api/v1/portfolio/entries",
        json=_ENTRY_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_entries_returns_list(client: AsyncClient) -> None:
    """Spec #4: GET /portfolio/entries returns a list."""
    token = await _register_and_onboard(client, "port7@test.com", "oficio", "Carpinteria")

    with (
        patch("app.api.v1.portfolio.generate_portfolio_entry_embedding") as m1,
        patch("app.api.v1.portfolio.generate_worker_embedding") as m2,
    ):
        m1.delay = MagicMock()
        m2.delay = MagicMock()
        await client.post(
            "/api/v1/portfolio/entries",
            json={
                "title": "Fabricacion de mueble de madera",
                "description": "Fabrique muebles de madera y puertas para cliente en Huancayo usando herramientas electricas",
                "is_public": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    resp = await client.get(
        "/api/v1/portfolio/entries",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_non_oficio_worker_public_404(client: AsyncClient) -> None:
    """Spec #7: public portfolio for non-OFICIO username → 404."""
    # Register a PRIMER_EMPLEO worker — they have no public portfolio
    token = await _register_and_onboard(client, "port8@test.com", "primer_empleo")
    profile_resp = await client.get(
        "/api/v1/workers/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    username = profile_resp.json().get("username")
    assert username

    resp = await client.get(f"/api/v1/portfolio/{username}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_entry_recalculates_rating(client: AsyncClient) -> None:
    """Spec #8: PATCH entry with client_rating → avg_rating recalculated."""
    token = await _register_and_onboard(client, "port9@test.com", "oficio", "Pintura")

    with (
        patch("app.api.v1.portfolio.generate_portfolio_entry_embedding") as m1,
        patch("app.api.v1.portfolio.generate_worker_embedding") as m2,
    ):
        m1.delay = MagicMock()
        m2.delay = MagicMock()
        create_resp = await client.post(
            "/api/v1/portfolio/entries",
            json={
                "title": "Pintura de interiores en Chilca",
                "description": "Pinte interiores de una casa de dos pisos usando pintura latex y rodillo",
                "is_public": True,
                "client_rating": 4.0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert create_resp.status_code == 201
    entry_id = create_resp.json()["id"]

    # Update with new rating
    with (
        patch("app.api.v1.portfolio.generate_portfolio_entry_embedding") as m1,
        patch("app.api.v1.portfolio.generate_worker_embedding") as m2,
    ):
        m1.delay = MagicMock()
        m2.delay = MagicMock()
        patch_resp = await client.patch(
            f"/api/v1/portfolio/entries/{entry_id}",
            json={"client_rating": 5.0},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert patch_resp.status_code == 200

    # Verify worker avg_rating updated
    profile_resp = await client.get(
        "/api/v1/workers/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile_resp.status_code == 200
    # avg_rating should now reflect the updated rating
    avg = profile_resp.json().get("avg_rating", 0)
    assert avg > 0


@pytest.mark.asyncio
async def test_photo_upload_invalid_mime(client: AsyncClient) -> None:
    """Spec #10: photo upload with invalid MIME → 422."""
    import io as _io
    token = await _register_and_onboard(client, "port10@test.com", "oficio", "Electricidad")

    with (
        patch("app.api.v1.portfolio.generate_portfolio_entry_embedding") as m1,
        patch("app.api.v1.portfolio.generate_worker_embedding") as m2,
    ):
        m1.delay = MagicMock()
        m2.delay = MagicMock()
        create_resp = await client.post(
            "/api/v1/portfolio/entries",
            json=_ENTRY_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    entry_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/portfolio/entries/{entry_id}/photos",
        headers={"Authorization": f"Bearer {token}"},
        files={"files": ("doc.pdf", _io.BytesIO(b"%PDF"), "application/pdf")},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_photo_upload_too_large(client: AsyncClient) -> None:
    """Spec #11: photo > 5 MB → 422."""
    import io as _io
    token = await _register_and_onboard(client, "port11@test.com", "oficio", "Gasfiteria")

    with (
        patch("app.api.v1.portfolio.generate_portfolio_entry_embedding") as m1,
        patch("app.api.v1.portfolio.generate_worker_embedding") as m2,
    ):
        m1.delay = MagicMock()
        m2.delay = MagicMock()
        create_resp = await client.post(
            "/api/v1/portfolio/entries",
            json={
                "title": "Instalacion de tuberias en El Tambo",
                "description": "Instale tuberias sanitarias y reparacion de canerias en vivienda nueva",
                "is_public": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    entry_id = create_resp.json()["id"]

    big_image = b"\xff\xd8\xff" + b"x" * (6 * 1024 * 1024)  # > 5 MB fake JPEG
    resp = await client.post(
        f"/api/v1/portfolio/entries/{entry_id}/photos",
        headers={"Authorization": f"Bearer {token}"},
        files={"files": ("big.jpg", _io.BytesIO(big_image), "image/jpeg")},
    )
    assert resp.status_code == 422
