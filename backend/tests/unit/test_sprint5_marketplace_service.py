# RF: RF118-RF125 — Tests para marketplace_service (Sprint 5)
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.marketplace import ServiceListingCreate, ServiceListingUpdate


def _make_worker(**kwargs):
    w = MagicMock()
    w.id = kwargs.get("id", "worker-1")
    w.full_name = None
    w.district = kwargs.get("district", "Huancayo")
    w.avg_rating = Decimal("4.5")
    w.years_experience = 3
    w.username = "tester"
    w.worker_type = "oficio"
    w.dni = b""
    w.user_id = "user-1"
    return w


def _make_listing(**kwargs):
    lst = MagicMock()
    lst.id = kwargs.get("id", "listing-1")
    lst.worker_id = kwargs.get("worker_id", "worker-1")
    lst.trade_category = kwargs.get("trade_category", "Electricidad")
    lst.title = kwargs.get("title", "Instalación eléctrica")
    lst.description = kwargs.get("description", "Instalación completa para casas")
    lst.enriched_keywords = kwargs.get("enriched_keywords", ["electricidad"])
    lst.districts = kwargs.get("districts", ["Huancayo"])
    lst.price_reference = Decimal("100.00")
    lst.price_unit = "hora"
    lst.availability = kwargs.get("availability", "inmediata")
    lst.is_active = True
    lst.views_count = 0
    lst.created_at = datetime(2026, 5, 12)
    return lst


# ── create_listing ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_listing_adds_and_returns_response():
    from app.services.marketplace.marketplace_service import create_listing

    db = AsyncMock()
    worker = _make_worker()
    listing_obj = _make_listing()
    db.refresh = AsyncMock()

    body = ServiceListingCreate(
        trade_category="Electricidad",
        title="Instalación eléctrica residencial",
        description="Instalo tomacorrientes y tableros eléctricos",
        districts=["Huancayo"],
        availability="inmediata",
    )

    with patch("app.services.marketplace.marketplace_service.extract_skills_from_job_description") as mock_extract, \
         patch("app.services.marketplace.marketplace_service.ServiceListing", return_value=listing_obj), \
         patch("app.services.marketplace.marketplace_service.generate_listing_embedding", create=True):
        mock_extract.return_value = MagicMock(skills=["instalación eléctrica", "tableros"])
        result = await create_listing(worker, body, db)

    assert result.trade_category == listing_obj.trade_category
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_listing_celery_failure_does_not_raise():
    from app.services.marketplace.marketplace_service import create_listing

    db = AsyncMock()
    worker = _make_worker()
    listing_obj = _make_listing()

    body = ServiceListingCreate(
        trade_category="Gasfitería",
        title="Arreglo de cañerías en baños",
        description="Reparo tuberías y cañerías con garantía",
        districts=["El Tambo"],
    )

    with patch("app.services.marketplace.marketplace_service.extract_skills_from_job_description") as mock_e, \
         patch("app.services.marketplace.marketplace_service.ServiceListing", return_value=listing_obj), \
         patch("app.tasks.embeddings.generate_listing_embedding") as mock_task:
        mock_e.return_value = MagicMock(skills=[])
        mock_task.delay.side_effect = Exception("Celery unavailable")
        result = await create_listing(worker, body, db)

    assert result is not None


# ── delete_listing ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_listing_sets_inactive():
    from app.services.marketplace.marketplace_service import delete_listing

    db = AsyncMock()
    listing = _make_listing()
    r = MagicMock()
    r.scalar_one_or_none.return_value = listing
    db.execute.return_value = r

    result = await delete_listing("listing-1", "worker-1", db)

    assert result is True
    assert listing.is_active is False
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_listing_not_found_returns_false():
    from app.services.marketplace.marketplace_service import delete_listing

    db = AsyncMock()
    r = MagicMock()
    r.scalar_one_or_none.return_value = None
    db.execute.return_value = r

    result = await delete_listing("listing-x", "worker-1", db)
    assert result is False


# ── get_listing ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_listing_increments_views():
    from app.services.marketplace.marketplace_service import get_listing

    db = AsyncMock()
    listing = _make_listing(views_count=5)
    worker = _make_worker()

    r1, r2 = MagicMock(), MagicMock()
    r1.scalar_one_or_none.return_value = listing
    r2.scalar_one_or_none.return_value = worker
    db.execute.side_effect = [r1, r2]

    result = await get_listing("listing-1", db)
    assert listing.views_count == 1  # 0 + 1 (MagicMock default is 0)
    assert result is not None


@pytest.mark.asyncio
async def test_get_listing_not_found_returns_none():
    from app.services.marketplace.marketplace_service import get_listing

    db = AsyncMock()
    r = MagicMock()
    r.scalar_one_or_none.return_value = None
    db.execute.return_value = r

    result = await get_listing("missing", db)
    assert result is None


# ── search_listings (no query) ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_listings_no_query_returns_list():
    from app.services.marketplace.marketplace_service import search_listings

    db = AsyncMock()
    listing = _make_listing()
    worker = _make_worker()

    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [listing]
    r1 = MagicMock()
    r1.scalars.return_value = scalars_mock

    r2 = MagicMock()
    r2.scalar_one_or_none.return_value = worker
    db.execute.side_effect = [r1, r2]

    results = await search_listings(
        query=None, districts=None, trade_category=None,
        availability=None, limit=10, offset=0, db=db,
    )
    assert len(results) == 1


@pytest.mark.asyncio
async def test_search_listings_no_query_empty():
    from app.services.marketplace.marketplace_service import search_listings

    db = AsyncMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = []
    r = MagicMock()
    r.scalars.return_value = scalars_mock
    db.execute.return_value = r

    results = await search_listings(
        query=None, districts=None, trade_category=None,
        availability=None, limit=10, offset=0, db=db,
    )
    assert results == []


# ── update_listing ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_listing_not_found_returns_none():
    from app.services.marketplace.marketplace_service import update_listing

    db = AsyncMock()
    r = MagicMock()
    r.scalar_one_or_none.return_value = None
    db.execute.return_value = r

    result = await update_listing("x", "w", ServiceListingUpdate(title="Nuevo título"), db)
    assert result is None


@pytest.mark.asyncio
async def test_update_listing_updates_fields():
    from app.services.marketplace.marketplace_service import update_listing

    db = AsyncMock()
    listing = _make_listing()
    worker = _make_worker()

    r1 = MagicMock()
    r1.scalar_one_or_none.return_value = listing
    r2 = MagicMock()
    r2.scalar_one_or_none.return_value = worker
    db.execute.side_effect = [r1, r2]

    with patch("app.services.marketplace.marketplace_service.extract_skills_from_job_description") as mock_e:
        mock_e.return_value = MagicMock(skills=["nueva habilidad"])
        result = await update_listing(
            "listing-1", "worker-1",
            ServiceListingUpdate(description="Nueva descripción detallada para testing"),
            db,
        )

    assert result is not None
    db.commit.assert_called_once()
