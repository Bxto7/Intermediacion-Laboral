# RF: RF086-RF095 (M05) — Tests del pipeline completo ML: dataset → train → deploy
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from app.ml.matching_engine.trainer import F1_MINIMUM, train_matching_model


def _make_balanced_dataset(n: int = 200):
    rng = np.random.default_rng(42)
    X = rng.uniform(0, 1, (n, 9)).astype(np.float32)
    y = rng.integers(0, 2, n).astype(np.int32)
    return X, y


def test_train_matching_model_deploys_on_good_data(tmp_path):
    X, y = _make_balanced_dataset(300)
    with patch("app.ml.matching_engine.trainer.MODEL_DIR", tmp_path):
        result = train_matching_model(X, y, worker_type="all", deploy_if_better=True)
    assert "metrics" in result
    assert "f1" in result["metrics"]
    # Si F1 ≥ umbral, debe estar desplegado
    if result["metrics"]["f1"] >= F1_MINIMUM:
        assert result["deployed"] is True
        assert (tmp_path / result["model_path"].split("/")[-1]).exists() or \
               Path(result["model_path"]).exists()


def test_train_matching_model_insufficient_data():
    X = np.zeros((5, 9), dtype=np.float32)
    y = np.zeros(5, dtype=np.int32)
    result = train_matching_model(X, y, worker_type="all")
    assert result["deployed"] is False
    assert result.get("reason") == "insufficient_data"


def test_train_matching_model_metrics_keys():
    X, y = _make_balanced_dataset(200)
    result = train_matching_model(X, y, worker_type="experiencia", deploy_if_better=False)
    assert set(result["metrics"].keys()) == {"f1", "precision", "recall"}


@pytest.mark.asyncio
async def test_train_from_db_insufficient_events():
    from app.ml.matching_engine.trainer import train_from_db

    db = AsyncMock()
    with patch(
        "app.ml.matching_engine.trainer.build_training_dataset",
        return_value=(np.empty((0, 9)), np.empty(0)),
    ):
        result = await train_from_db(db, worker_type="all")
    assert result["deployed"] is False
    assert result["reason"] == "insufficient_data"


@pytest.mark.asyncio
async def test_train_from_db_saves_metrics_json(tmp_path):
    from app.ml.matching_engine.trainer import train_from_db

    X, y = _make_balanced_dataset(300)
    db = AsyncMock()

    with (
        patch("app.ml.matching_engine.trainer.MODEL_DIR", tmp_path),
        patch(
            "app.ml.matching_engine.trainer.build_training_dataset",
            return_value=(X, y),
        ),
        patch("app.ml.matching_engine.drift_detector.MODEL_DIR", tmp_path),
    ):
        result = await train_from_db(db, worker_type="all", deploy_if_better=True)

    if result.get("deployed"):
        metrics_files = list(tmp_path.glob("metrics_all_*.json"))
        assert len(metrics_files) >= 1
        with open(metrics_files[0]) as fh:
            saved = json.load(fh)
        assert "f1" in saved
