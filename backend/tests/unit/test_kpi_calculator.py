# RF: RF136-RF145 (M09) — Tests del calculador de KPIs institucionales
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.reports.kpi_calculator import (
    calculate_ivm,
    calculate_rbs,
    calculate_tcc,
    calculate_tcss,
    calculate_tf,
    calculate_vil,
)


def _mock_db(rows):
    db = AsyncMock()
    result = MagicMock()
    result.fetchall.return_value = rows
    result.fetchone.return_value = rows[0] if rows else None
    db.execute.return_value = result
    return db


def _row(**kwargs):
    r = MagicMock()
    for k, v in kwargs.items():
        setattr(r, k, v)
    return r


@pytest.mark.asyncio
async def test_calculate_vil_empty():
    db = _mock_db([])
    result = await calculate_vil(db)
    assert result == {}


@pytest.mark.asyncio
async def test_calculate_vil_returns_per_type():
    rows = [
        _row(worker_type="primer_empleo", avg_days=15.5, n=10),
        _row(worker_type="experiencia", avg_days=8.2, n=25),
    ]
    db = _mock_db(rows)
    result = await calculate_vil(db)
    assert "primer_empleo" in result
    assert result["primer_empleo"]["avg_days"] == 15.5
    assert result["experiencia"]["n"] == 25


@pytest.mark.asyncio
async def test_calculate_tf_returns_percentage():
    rows = [_row(worker_type="oficio", tf_pct=42.5)]
    db = _mock_db(rows)
    result = await calculate_tf(db)
    assert result["oficio"] == 42.5


@pytest.mark.asyncio
async def test_calculate_tcc_returns_percentage():
    rows = [
        _row(worker_type="primer_empleo", tcc_pct=68.0),
        _row(worker_type="oficio", tcc_pct=55.0),
    ]
    db = _mock_db(rows)
    result = await calculate_tcc(db)
    assert result["primer_empleo"] == 68.0


@pytest.mark.asyncio
async def test_calculate_ivm_no_oficio():
    db = AsyncMock()
    result = MagicMock()
    result.fetchone.return_value = None
    db.execute.return_value = result
    result = await calculate_ivm(db)
    assert result["ivm_pct"] == 0.0
    assert result["total_oficio"] == 0


@pytest.mark.asyncio
async def test_calculate_ivm_with_data():
    db = AsyncMock()
    result = MagicMock()
    result.fetchone.return_value = _row(ivm_pct=78.5, total_oficio=40)
    db.execute.return_value = result
    result = await calculate_ivm(db)
    assert result["ivm_pct"] == 78.5
    assert result["total_oficio"] == 40


@pytest.mark.asyncio
async def test_calculate_tcss_returns_per_type():
    rows = [
        _row(worker_type="primer_empleo", tcss_pct=61.0),
        _row(worker_type="oficio", tcss_pct=73.0),
    ]
    db = _mock_db(rows)
    result = await calculate_tcss(db)
    assert result["oficio"] == 73.0


@pytest.mark.asyncio
async def test_calculate_rbs_no_data():
    db = _mock_db([])
    result = await calculate_rbs(db)
    assert result["avg_pct"] == 0.0
    assert result["n_pairs"] == 0


@pytest.mark.asyncio
async def test_calculate_rbs_with_valid_pairs():
    from app.core.security import encrypt_field

    pre_income = encrypt_field("1000.0")
    post_income = encrypt_field("1300.0")
    rows = [
        _row(worker_id="uuid-1", survey_phase="pre", monthly_income=pre_income),
        _row(worker_id="uuid-1", survey_phase="post", monthly_income=post_income),
    ]
    db = _mock_db(rows)
    result = await calculate_rbs(db)
    assert result["n_pairs"] == 1
    assert abs(result["avg_pct"] - 30.0) < 0.1
