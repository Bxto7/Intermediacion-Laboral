# RF: RF161-RF165 (M12) — Tests del conector DRTPE-Junín (stub)
import pytest

from app.integrations.drtpe.connector import DRTPEConnectorStub, drtpe_connector


@pytest.mark.asyncio
async def test_fetch_active_offers_returns_list():
    stub = DRTPEConnectorStub()
    offers = await stub.fetch_active_offers()
    assert isinstance(offers, list)
    assert len(offers) > 0


@pytest.mark.asyncio
async def test_fetch_active_offers_limit():
    stub = DRTPEConnectorStub()
    offers = await stub.fetch_active_offers(limit=2)
    assert len(offers) == 2


@pytest.mark.asyncio
async def test_fetch_active_offers_fields():
    stub = DRTPEConnectorStub()
    offers = await stub.fetch_active_offers(limit=1)
    offer = offers[0]
    assert offer.external_id.startswith("DRTPE-")
    assert offer.source == "DRTPE-JUNIN"
    assert isinstance(offer.required_skills, list)
    assert offer.salary_min is not None


@pytest.mark.asyncio
async def test_sync_worker_registration_returns_true():
    stub = DRTPEConnectorStub()
    result = await stub.sync_worker_registration("worker-123", {"name": "Test"})
    assert result is True


@pytest.mark.asyncio
async def test_report_placement_returns_true():
    stub = DRTPEConnectorStub()
    result = await stub.report_placement("contract-456", {"status": "signed"})
    assert result is True


def test_singleton_is_stub_instance():
    assert isinstance(drtpe_connector, DRTPEConnectorStub)


@pytest.mark.asyncio
async def test_all_offers_have_junin_districts():
    stub = DRTPEConnectorStub()
    offers = await stub.fetch_active_offers()
    known_districts = {"Huancayo", "El Tambo", "Chilca"}
    for offer in offers:
        assert offer.district in known_districts, f"Distrito inesperado: {offer.district}"
