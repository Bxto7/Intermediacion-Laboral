# RF: RF041-RF055 — Tests para applications, contracts, ratings (Sprint 5)
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.contract import ContractStatusUpdate, RatingCreate


def _make_worker(**kw):
    w = MagicMock()
    w.id = kw.get("id", "worker-1")
    w.user_id = kw.get("user_id", "user-1")
    w.avg_rating = Decimal("4.0")
    return w


def _make_contract(**kw):
    c = MagicMock()
    c.id = kw.get("id", "contract-1")
    c.job_request_id = kw.get("job_request_id", "jr-1")
    c.worker_id = kw.get("worker_id", "worker-1")
    c.employer_id = kw.get("employer_id", "emp-1")
    c.status = kw.get("status", "CONFIRMED")
    c.agreed_rate = Decimal("50.00")
    c.rate_type = "hora"
    c.start_date = date(2026, 5, 1)
    c.end_date = None
    c.final_amount = None
    c.payment_method = None
    c.payment_confirmed = False
    c.cancelled_reason = None
    c.created_at = datetime(2026, 5, 1)
    return c


def _make_application(**kw):
    a = MagicMock()
    a.id = kw.get("id", "app-1")
    a.job_request_id = kw.get("job_request_id", "offer-1")
    a.worker_id = kw.get("worker_id", "worker-1")
    a.status = kw.get("status", "PENDING")
    a.message = "Me interesa esta oferta"
    a.proposed_rate = Decimal("45.00")
    a.created_at = datetime(2026, 5, 10)
    return a


# ── _build_contract_response ────────────────────────────────────────────────

def test_build_contract_response_returns_correct_fields():
    from app.api.v1.contracts import _build_contract_response

    contract = _make_contract()
    resp = _build_contract_response(contract)
    assert resp.id == "contract-1"
    assert resp.worker_id == "worker-1"
    assert resp.payment_confirmed is False


# ── ContractStatusUpdate schema ──────────────────────────────────────────────

def test_contract_status_update_valid():
    body = ContractStatusUpdate(status="COMPLETED")
    assert body.status == "COMPLETED"


def test_contract_status_update_invalid():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ContractStatusUpdate(status="UNKNOWN_STATUS")


def test_contract_status_update_cancelled_with_reason():
    body = ContractStatusUpdate(status="CANCELLED", cancelled_reason="Cliente canceló")
    assert body.cancelled_reason == "Cliente canceló"


# ── RatingCreate schema ──────────────────────────────────────────────────────

def test_rating_create_valid():
    from uuid import uuid4
    r = RatingCreate(
        contract_id=uuid4(),
        rated_id=uuid4(),
        overall_score=4.5,
        comment="Excelente trabajo",
    )
    assert r.overall_score == 4.5


def test_rating_create_invalid_score_too_high():
    from uuid import uuid4
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        RatingCreate(contract_id=uuid4(), rated_id=uuid4(), overall_score=6.0)


def test_rating_create_invalid_score_too_low():
    from uuid import uuid4
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        RatingCreate(contract_id=uuid4(), rated_id=uuid4(), overall_score=0.5)


# ── get_my_contracts ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_my_contracts_returns_list():
    from app.api.v1.contracts import get_my_contracts

    worker = _make_worker()
    contract = _make_contract()

    db = AsyncMock()
    r_worker = MagicMock(); r_worker.scalar_one_or_none.return_value = worker
    scalars_mock = MagicMock(); scalars_mock.all.return_value = [contract]
    r_contracts = MagicMock(); r_contracts.scalars.return_value = scalars_mock
    db.execute.side_effect = [r_worker, r_contracts]

    result = await get_my_contracts(payload={"sub": "user-1"}, db=db)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_my_contracts_worker_not_found_raises_404():
    from fastapi import HTTPException
    from app.api.v1.contracts import get_my_contracts

    db = AsyncMock()
    r = MagicMock(); r.scalar_one_or_none.return_value = None
    db.execute.return_value = r

    with pytest.raises(HTTPException) as exc:
        await get_my_contracts(payload={"sub": "user-x"}, db=db)
    assert exc.value.status_code == 404


# ── update_contract_status ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_status_to_completed_sets_payment_confirmed():
    from app.api.v1.contracts import update_contract_status

    worker = _make_worker()
    contract = _make_contract(status="IN_PROGRESS")

    db = AsyncMock()
    r_worker = MagicMock(); r_worker.scalar_one_or_none.return_value = worker
    r_contract = MagicMock(); r_contract.scalar_one_or_none.return_value = contract
    db.execute.side_effect = [r_worker, r_contract]

    body = ContractStatusUpdate(status="COMPLETED", final_amount=500.0)

    with patch("app.integrations.drtpe.connector.drtpe_connector") as mock_drtpe:
        mock_drtpe.report_placement = AsyncMock(return_value=True)
        result = await update_contract_status("contract-1", body, {"sub": "user-1"}, db)

    assert result.status == "COMPLETED"
    assert contract.payment_confirmed is True


@pytest.mark.asyncio
async def test_update_status_drtpe_failure_does_not_raise():
    from app.api.v1.contracts import update_contract_status

    worker = _make_worker()
    contract = _make_contract(status="IN_PROGRESS")

    db = AsyncMock()
    r_worker = MagicMock(); r_worker.scalar_one_or_none.return_value = worker
    r_contract = MagicMock(); r_contract.scalar_one_or_none.return_value = contract
    db.execute.side_effect = [r_worker, r_contract]

    body = ContractStatusUpdate(status="COMPLETED")

    with patch("app.integrations.drtpe.connector.drtpe_connector") as mock_drtpe:
        mock_drtpe.report_placement = AsyncMock(side_effect=RuntimeError("DRTPE down"))
        result = await update_contract_status("contract-1", body, {"sub": "user-1"}, db)

    assert result.status == "COMPLETED"


@pytest.mark.asyncio
async def test_update_status_cancelled_saves_reason():
    from app.api.v1.contracts import update_contract_status

    worker = _make_worker()
    contract = _make_contract(status="CONFIRMED")

    db = AsyncMock()
    r_worker = MagicMock(); r_worker.scalar_one_or_none.return_value = worker
    r_contract = MagicMock(); r_contract.scalar_one_or_none.return_value = contract
    db.execute.side_effect = [r_worker, r_contract]

    body = ContractStatusUpdate(status="CANCELLED", cancelled_reason="Trabajo terminado")
    result = await update_contract_status("contract-1", body, {"sub": "user-1"}, db)

    assert contract.cancelled_reason == "Trabajo terminado"
    assert result.status == "CANCELLED"


# ── applications ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_withdraw_pending_application_sets_withdrawn():
    from app.api.v1.applications import withdraw_application

    worker = _make_worker()
    app = _make_application(status="PENDING")

    db = AsyncMock()
    r_worker = MagicMock(); r_worker.scalar_one_or_none.return_value = worker
    r_app = MagicMock(); r_app.scalar_one_or_none.return_value = app
    db.execute.side_effect = [r_worker, r_app]

    await withdraw_application("app-1", {"sub": "user-1"}, db)
    assert app.status == "WITHDRAWN"


@pytest.mark.asyncio
async def test_withdraw_accepted_application_raises_409():
    from fastapi import HTTPException
    from app.api.v1.applications import withdraw_application

    worker = _make_worker()
    app = _make_application(status="ACCEPTED")

    db = AsyncMock()
    r_worker = MagicMock(); r_worker.scalar_one_or_none.return_value = worker
    r_app = MagicMock(); r_app.scalar_one_or_none.return_value = app
    db.execute.side_effect = [r_worker, r_app]

    with pytest.raises(HTTPException) as exc:
        await withdraw_application("app-1", {"sub": "user-1"}, db)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_get_my_applications_empty_list():
    from app.api.v1.applications import get_my_applications

    worker = _make_worker()
    db = AsyncMock()
    r_worker = MagicMock(); r_worker.scalar_one_or_none.return_value = worker
    scalars_mock = MagicMock(); scalars_mock.all.return_value = []
    r_apps = MagicMock(); r_apps.scalars.return_value = scalars_mock
    db.execute.side_effect = [r_worker, r_apps]

    result = await get_my_applications({"sub": "user-1"}, db)
    assert result == []


# ── create_rating ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_rating_on_non_completed_contract_raises_409():
    from fastapi import HTTPException
    from uuid import uuid4
    from app.api.v1.contracts import create_rating

    db = AsyncMock()

    user = MagicMock(); user.id = "user-1"
    contract = _make_contract(status="IN_PROGRESS", worker_id="worker-1")

    r_user = MagicMock(); r_user.scalar_one_or_none.return_value = user
    r_contract = MagicMock(); r_contract.scalar_one_or_none.return_value = contract
    db.execute.side_effect = [r_user, r_contract]

    body = RatingCreate(
        contract_id=uuid4(),
        rated_id=uuid4(),
        overall_score=4.0,
    )
    with pytest.raises(HTTPException) as exc:
        await create_rating(body, {"sub": "user-1"}, db)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_create_rating_duplicate_raises_409():
    from fastapi import HTTPException
    from uuid import uuid4
    from app.api.v1.contracts import create_rating

    db = AsyncMock()
    user = MagicMock(); user.id = "user-1"
    contract = _make_contract(status="COMPLETED", worker_id="user-1")
    existing_rating = MagicMock()

    r_user = MagicMock(); r_user.scalar_one_or_none.return_value = user
    r_contract = MagicMock(); r_contract.scalar_one_or_none.return_value = contract
    r_existing = MagicMock(); r_existing.scalar_one_or_none.return_value = existing_rating
    db.execute.side_effect = [r_user, r_contract, r_existing]

    body = RatingCreate(
        contract_id=uuid4(),
        rated_id=uuid4(),
        overall_score=3.0,
    )
    with pytest.raises(HTTPException) as exc:
        await create_rating(body, {"sub": "user-1"}, db)
    assert exc.value.status_code == 409
