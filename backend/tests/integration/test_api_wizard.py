# RF: RF096-RF110
"""Integration tests for 6-step CV wizard (PRIMER_EMPLEO only)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


async def _register_and_onboard(
    client: AsyncClient,
    email: str,
    worker_type: str,
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
    else:
        payload = {"is_first_job": False, "is_trade_worker": False}

    await client.post(
        "/api/v1/onboarding/detect-type",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    return token


async def _submit_step(
    client: AsyncClient, token: str, step: int, data: dict
):
    return await client.post(
        "/api/v1/wizard/step",
        json={"step": step, "data": data},
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest.mark.asyncio
async def test_get_wizard_progress_returns_current_state(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "wiz0@test.com", "primer_empleo")
    resp = await client.get(
        "/api/v1/wizard/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "current_step" in data
    assert "is_complete" in data
    assert "extracted_skills" in data


@pytest.mark.asyncio
async def test_step1_saves_progress(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "wiz1@test.com", "primer_empleo")
    resp = await _submit_step(
        client, token, 1, {"full_name": "Juan Perez", "district": "Huancayo"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_step"] >= 1
    assert data["is_complete"] is False


@pytest.mark.asyncio
async def test_step3_extracts_skills_from_free_text(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "wiz2@test.com", "primer_empleo")

    await _submit_step(
        client, token, 1, {"full_name": "Maria Garcia", "district": "El Tambo"}
    )
    await _submit_step(
        client, token, 2, {"education_level": "secundaria", "institution": "Colegio San Pedro"}
    )
    resp = await _submit_step(
        client,
        token,
        3,
        {
            "text": (
                "soy muy puntual y responsable, trabajo bien en equipo "
                "y ayudo a mi familia con carpinteria y trabajos manuales"
            )
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["extracted_skills"], list)


@pytest.mark.asyncio
async def test_cannot_skip_steps(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "wiz3@test.com", "primer_empleo")
    resp = await _submit_step(
        client, token, 3, {"text": "quiero saltar pasos"}
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_summary_requires_step6_complete(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "wiz4@test.com", "primer_empleo")

    await _submit_step(
        client, token, 1, {"full_name": "Carlos Lopez", "district": "Chilca"}
    )
    await _submit_step(
        client, token, 2, {"education_level": "tecnica", "institution": "SENATI"}
    )

    resp = await client.get(
        "/api/v1/wizard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "completo" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_wizard_requires_primer_empleo_type(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "wiz5@test.com", "experiencia")
    resp = await _submit_step(
        client, token, 1, {"full_name": "Ana Torres", "district": "Huancayo"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_progress_creates_if_not_exists(client: AsyncClient) -> None:
    """Spec #1: GET wizard progress for new user creates initial state."""
    token = await _register_and_onboard(client, "wiz_new@test.com", "primer_empleo")
    resp = await client.get(
        "/api/v1/wizard/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_step"] >= 1
    assert data["is_complete"] is False


@pytest.mark.asyncio
async def test_step_1_saves_data(client: AsyncClient) -> None:
    """Spec #2: step 1 data persists and is retrievable."""
    token = await _register_and_onboard(client, "wiz_s1@test.com", "primer_empleo")
    resp = await _submit_step(
        client, token, 1, {"full_name": "Lucia Condori", "district": "El Tambo"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_step"] >= 1

    # Verify progress was saved
    progress_resp = await client.get(
        "/api/v1/wizard/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert progress_resp.status_code == 200
    progress = progress_resp.json()
    assert progress["current_step"] >= 1


@pytest.mark.asyncio
async def test_step_3_extracts_skills(client: AsyncClient) -> None:
    """Spec #3: step 3 with free text → extracted_skills populated."""
    token = await _register_and_onboard(client, "wiz_s3@test.com", "primer_empleo")
    await _submit_step(client, token, 1, {"full_name": "Jorge Lima", "district": "Huancayo"})
    await _submit_step(client, token, 2, {"education_level": "secundaria", "institution": "Colegio Nacional"})
    resp = await _submit_step(
        client, token, 3, {"text": "soy puntual y trabajador, ayudo a mi papa en carpinteria"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["extracted_skills"], list)
    assert len(data["extracted_skills"]) > 0


@pytest.mark.asyncio
async def test_step_6_updates_completeness(client: AsyncClient) -> None:
    """Spec #5: completing step 6 sets is_complete=True and updates profile_completeness."""
    token = await _register_and_onboard(client, "wiz_s6@test.com", "primer_empleo")
    await _submit_step(client, token, 1, {"full_name": "Elena Quispe", "district": "Chilca"})
    await _submit_step(client, token, 2, {"education_level": "tecnica", "institution": "SENATI Huancayo"})
    await _submit_step(client, token, 3, {"text": "soy responsable y puntual, trabajo bien en equipo"})
    await _submit_step(client, token, 4, {"text": "ayude en la panaderia familiar haciendo pan y atendiendo clientes"})
    await _submit_step(client, token, 5, {"interests": ["gastronomia", "comercio"]})

    with patch("app.tasks.embeddings.generate_worker_embedding") as mock_embed:
        mock_embed.delay = MagicMock()
        resp6 = await _submit_step(client, token, 6, {"preview_accepted": True})

    assert resp6.status_code == 200
    assert resp6.json()["is_complete"] is True

    # Verify profile_completeness increased
    profile_resp = await client.get(
        "/api/v1/workers/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile_resp.status_code == 200
    assert profile_resp.json()["profile_completeness"] > 0


@pytest.mark.asyncio
async def test_summary_returns_skills(client: AsyncClient) -> None:
    """Spec #8: after completing wizard, summary contains skills."""
    token = await _register_and_onboard(client, "wiz_sum@test.com", "primer_empleo")
    await _submit_step(client, token, 1, {"full_name": "Pedro Torres", "district": "Huancayo"})
    await _submit_step(client, token, 2, {"education_level": "secundaria", "institution": "Colegio Salesiano"})
    await _submit_step(client, token, 3, {"text": "soy puntual y me gusta el trabajo en equipo y comercio"})
    await _submit_step(client, token, 4, {"text": "vendo en el mercado y manejo caja registradora"})
    await _submit_step(client, token, 5, {"interests": ["comercio", "ventas"]})

    with patch("app.tasks.embeddings.generate_worker_embedding") as mock_embed:
        mock_embed.delay = MagicMock()
        await _submit_step(client, token, 6, {"preview_accepted": True})

    summary_resp = await client.get(
        "/api/v1/wizard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert summary_resp.status_code == 200
    data = summary_resp.json()
    assert "skills" in data
    assert isinstance(data["skills"], list)
    assert len(data["skills"]) > 0


@pytest.mark.asyncio
async def test_complete_wizard_and_get_summary(client: AsyncClient) -> None:
    token = await _register_and_onboard(client, "wiz6@test.com", "primer_empleo")

    await _submit_step(client, token, 1, {"full_name": "Rosa Lima", "district": "Huancayo"})
    await _submit_step(client, token, 2, {"education_level": "secundaria", "institution": "Colegio Salesiano"})
    await _submit_step(client, token, 3, {"text": "soy puntual y responsable, me gusta el trabajo en equipo"})
    await _submit_step(client, token, 4, {"text": "ayude en la tienda de mi familia y organice inventarios"})
    await _submit_step(client, token, 5, {"interests": ["comercio", "administracion"]})

    with patch("app.tasks.embeddings.generate_worker_embedding") as mock_embed:
        mock_embed.delay = MagicMock()
        resp6 = await _submit_step(client, token, 6, {"preview_accepted": True})

    assert resp6.status_code == 200
    assert resp6.json()["is_complete"] is True

    summary_resp = await client.get(
        "/api/v1/wizard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert summary_resp.status_code == 200
    data = summary_resp.json()
    assert "skills" in data
    assert "suggested_sectors" in data
