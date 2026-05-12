# RF: RF086-RF095 (M05) — Tests del dataset builder
import uuid
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from app.ml.matching_engine.dataset_builder import MIN_SAMPLES, build_training_dataset


def _make_row(worker_type="experiencia", action="accepted"):
    r = MagicMock()
    r.cosine_sim = 0.75
    r.ml_score = 0.65
    r.reputation_score = 0.80
    r.combined_score = 0.72
    r.rank_position = 3
    r.worker_type = worker_type
    r.equity_flag = False
    r.action = action
    return r


@pytest.mark.asyncio
async def test_build_dataset_insufficient_data():
    db = AsyncMock()
    result = MagicMock()
    result.fetchall.return_value = [_make_row()] * (MIN_SAMPLES - 1)
    db.execute.return_value = result
    X, y = await build_training_dataset(db, worker_type="all")
    assert X.shape == (0, 9)
    assert y.shape == (0,)


@pytest.mark.asyncio
async def test_build_dataset_returns_correct_shape():
    rows = [_make_row("primer_empleo", "accepted")] * 40 + \
           [_make_row("oficio", "rejected")] * 30
    db = AsyncMock()
    result = MagicMock()
    result.fetchall.return_value = rows
    db.execute.return_value = result
    X, y = await build_training_dataset(db, worker_type="all")
    assert X.shape == (70, 9)
    assert y.shape == (70,)
    assert set(y.tolist()) == {0, 1}


@pytest.mark.asyncio
async def test_build_dataset_features_bounded():
    rows = [_make_row() for _ in range(MIN_SAMPLES + 10)]
    db = AsyncMock()
    result = MagicMock()
    result.fetchall.return_value = rows
    db.execute.return_value = result
    X, _ = await build_training_dataset(db)
    # rank_position_norm debe estar en [0, 1]
    assert np.all(X[:, 4] >= 0) and np.all(X[:, 4] <= 1)
    # flags binarios
    for col in [5, 6, 7, 8]:
        assert set(X[:, col].tolist()).issubset({0.0, 1.0})


@pytest.mark.asyncio
async def test_build_dataset_worker_type_flags():
    rows = [_make_row("oficio", "accepted")] * MIN_SAMPLES
    db = AsyncMock()
    result = MagicMock()
    result.fetchall.return_value = rows
    db.execute.return_value = result
    X, _ = await build_training_dataset(db, worker_type="oficio")
    # is_oficio flag (col 5) debe ser 1
    assert np.all(X[:, 5] == 1.0)
    assert np.all(X[:, 6] == 0.0)  # is_primer_empleo
    assert np.all(X[:, 7] == 0.0)  # is_experiencia
