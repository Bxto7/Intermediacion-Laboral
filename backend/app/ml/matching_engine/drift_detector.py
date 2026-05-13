# RF: RF146-RF150 (M10) — Detección de drift PSI (Population Stability Index)
from __future__ import annotations

from pathlib import Path

import numpy as np
import structlog

logger = structlog.get_logger()

MODEL_DIR = Path(__file__).parent.parent / "models"

# Umbrales PSI — CLAUDE.md § Motor ML/NLP
PSI_WARNING = 0.10
PSI_ALERT = 0.25

WORKER_TYPES = ["primer_empleo", "experiencia", "oficio", "all"]


def _psi_score(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    """Calcula el PSI entre dos distribuciones numéricas.

    PSI < 0.10  → sin cambio significativo
    PSI 0.10–0.25 → cambio moderado (advertencia)
    PSI > 0.25  → cambio mayor (requiere reentrenamiento)
    """
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    breakpoints = np.linspace(0, 1, buckets + 1)
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf

    expected_pct = np.histogram(expected, bins=breakpoints)[0] / len(expected)
    actual_pct = np.histogram(actual, bins=breakpoints)[0] / len(actual)

    # Evitar divisiones por cero
    expected_pct = np.where(expected_pct == 0, 1e-6, expected_pct)
    actual_pct = np.where(actual_pct == 0, 1e-6, actual_pct)

    psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(psi)


def _load_reference_scores(worker_type: str) -> np.ndarray | None:
    """Carga scores de referencia guardados junto al modelo."""
    ref_path = MODEL_DIR / f"reference_scores_{worker_type}.npy"
    if not ref_path.exists():
        return None
    return np.load(str(ref_path))


def save_reference_scores(scores: np.ndarray, worker_type: str) -> None:
    """Persiste los scores de entrenamiento como referencia para drift futuro."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    np.save(str(MODEL_DIR / f"reference_scores_{worker_type}.npy"), scores)
    logger.info("reference_scores_saved", worker_type=worker_type, n=len(scores))


def detect_score_drift(
    current_scores: np.ndarray,
    worker_type: str = "all",
) -> dict:
    """Detecta drift comparando scores actuales vs scores de referencia.

    Returns dict con: psi, status ('ok'|'warning'|'alert'), worker_type.
    """
    reference = _load_reference_scores(worker_type)
    if reference is None:
        logger.warning("no_reference_scores", worker_type=worker_type)
        return {"psi": None, "status": "no_reference", "worker_type": worker_type}

    psi = _psi_score(reference, current_scores)
    if psi > PSI_ALERT:
        status = "alert"
        logger.error(
            "drift_alert",
            worker_type=worker_type,
            psi=round(psi, 4),
            threshold=PSI_ALERT,
        )
    elif psi > PSI_WARNING:
        status = "warning"
        logger.warning(
            "drift_warning",
            worker_type=worker_type,
            psi=round(psi, 4),
            threshold=PSI_WARNING,
        )
    else:
        status = "ok"
        logger.info("drift_ok", worker_type=worker_type, psi=round(psi, 4))

    return {"psi": round(psi, 4), "status": status, "worker_type": worker_type}


def check_all_types_drift() -> dict:
    """Ejecuta la detección de drift para todos los worker_types con modelo activo.
    Retorna un dict keyed por worker_type."""
    results = {}
    for wtype in WORKER_TYPES:
        ref = _load_reference_scores(wtype)
        if ref is None:
            results[wtype] = {"psi": None, "status": "no_reference"}
            continue
        # Simula distribución actual leyendo scores del modelo activo si existen
        current_path = MODEL_DIR / f"current_scores_{wtype}.npy"
        if not current_path.exists():
            results[wtype] = {"psi": None, "status": "no_current"}
            continue
        current = np.load(str(current_path))
        results[wtype] = detect_score_drift(current, wtype)
    return results
