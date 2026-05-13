# RF: RF161-RF165 — Tests para DRTPEConnectorReal y _get_connector (Sprint 5)
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.drtpe.connector import (
    DRTPEConnectorReal,
    DRTPEConnectorStub,
    _get_connector,
)


# ── DRTPEConnectorReal.fetch_active_offers ───────────────────────────────────

@pytest.mark.asyncio
async def test_real_connector_fetch_parses_response():
    connector = DRTPEConnectorReal.__new__(DRTPEConnectorReal)
    connector._api_key = "test-key"

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "ofertas": [
            {
                "id": "EXT-001",
                "titulo": "Técnico electricista",
                "empresa": "Empresa SAC",
                "distrito": "El Tambo",
                "habilidades_requeridas": ["instalación eléctrica"],
                "salario_min": 1200.0,
                "salario_max": 1800.0,
                "fecha_publicacion": "2026-05-01",
            }
        ]
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        offers = await connector.fetch_active_offers(limit=5)

    assert len(offers) == 1
    assert offers[0].external_id == "EXT-001"
    assert offers[0].source == "DRTPE-JUNIN"
    assert offers[0].salary_min == 1200.0


@pytest.mark.asyncio
async def test_real_connector_fetch_falls_back_to_stub_on_error():
    connector = DRTPEConnectorReal.__new__(DRTPEConnectorReal)
    connector._api_key = "test-key"

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(side_effect=Exception("Network error"))
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        offers = await connector.fetch_active_offers(limit=2)

    # Should fall back to stub which returns known data
    assert len(offers) == 2
    assert all(o.source == "DRTPE-JUNIN" for o in offers)


# ── DRTPEConnectorReal.sync_worker_registration ──────────────────────────────

@pytest.mark.asyncio
async def test_real_connector_sync_worker_success():
    connector = DRTPEConnectorReal.__new__(DRTPEConnectorReal)
    connector._api_key = "test-key"

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await connector.sync_worker_registration("worker-1", {"name": "Test"})

    assert result is True


@pytest.mark.asyncio
async def test_real_connector_sync_worker_failure_returns_false():
    connector = DRTPEConnectorReal.__new__(DRTPEConnectorReal)
    connector._api_key = "test-key"

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(side_effect=Exception("timeout"))
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await connector.sync_worker_registration("worker-1", {})

    assert result is False


# ── DRTPEConnectorReal.report_placement ──────────────────────────────────────

@pytest.mark.asyncio
async def test_real_connector_report_placement_success():
    connector = DRTPEConnectorReal.__new__(DRTPEConnectorReal)
    connector._api_key = "test-key"

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await connector.report_placement("contract-1", {"status": "COMPLETED"})

    assert result is True


@pytest.mark.asyncio
async def test_real_connector_report_placement_failure_returns_false():
    connector = DRTPEConnectorReal.__new__(DRTPEConnectorReal)
    connector._api_key = "test-key"

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(side_effect=Exception("HTTP error"))
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await connector.report_placement("contract-1", {})

    assert result is False


# ── _get_connector ───────────────────────────────────────────────────────────

def test_get_connector_returns_stub_when_no_key():
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.DRTPE_API_KEY = ""
        connector = _get_connector()
    assert isinstance(connector, DRTPEConnectorStub)


def test_get_connector_returns_stub_when_key_is_stub():
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.DRTPE_API_KEY = "stub"
        connector = _get_connector()
    assert isinstance(connector, DRTPEConnectorStub)


def test_get_connector_returns_real_when_key_is_set():
    with patch("app.core.config.settings") as mock_settings, \
         patch.object(DRTPEConnectorReal, "__init__", return_value=None):
        mock_settings.DRTPE_API_KEY = "real-api-key-123"
        connector = _get_connector()
    assert isinstance(connector, DRTPEConnectorReal)
