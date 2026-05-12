# RF: RF146-RF150 (M10) — Tests PSI drift detector
import numpy as np
import pytest

from app.ml.matching_engine.drift_detector import (
    PSI_ALERT,
    PSI_WARNING,
    _psi_score,
    detect_score_drift,
    save_reference_scores,
)


def test_psi_identical_distributions():
    scores = np.linspace(0, 1, 200)
    psi = _psi_score(scores, scores)
    assert psi < PSI_WARNING, "Distribuciones idénticas deben tener PSI < 0.10"


def test_psi_very_different_distributions():
    expected = np.random.default_rng(42).uniform(0, 0.3, 300)
    actual = np.random.default_rng(42).uniform(0.7, 1.0, 300)
    psi = _psi_score(expected, actual)
    assert psi > PSI_ALERT, "Distribuciones opuestas deben superar el umbral de alerta"


def test_psi_empty_arrays():
    psi = _psi_score(np.array([]), np.array([0.5]))
    assert psi == 0.0


def test_detect_score_drift_no_reference(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.ml.matching_engine.drift_detector.MODEL_DIR", tmp_path
    )
    result = detect_score_drift(np.array([0.5, 0.6]), worker_type="all")
    assert result["status"] == "no_reference"
    assert result["psi"] is None


def test_detect_score_drift_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.ml.matching_engine.drift_detector.MODEL_DIR", tmp_path
    )
    ref = np.linspace(0.3, 0.7, 200)
    save_reference_scores(ref, "all")
    current = ref + np.random.default_rng(0).normal(0, 0.001, len(ref))
    result = detect_score_drift(current, worker_type="all")
    assert result["status"] == "ok"
    assert result["psi"] < PSI_WARNING


def test_detect_score_drift_warning(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.ml.matching_engine.drift_detector.MODEL_DIR", tmp_path
    )
    ref = np.linspace(0, 0.4, 300)
    save_reference_scores(ref, "primer_empleo")
    current = np.linspace(0.3, 0.8, 300)
    result = detect_score_drift(current, worker_type="primer_empleo")
    assert result["status"] in ("warning", "alert")


def test_detect_score_drift_alert(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.ml.matching_engine.drift_detector.MODEL_DIR", tmp_path
    )
    ref = np.zeros(300)
    save_reference_scores(ref, "oficio")
    current = np.ones(300)
    result = detect_score_drift(current, worker_type="oficio")
    assert result["status"] == "alert"
    assert result["psi"] > PSI_ALERT
