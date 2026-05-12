# RF: RF086-RF095 — Load the active ML model for inference
import pickle
from pathlib import Path

import structlog

logger = structlog.get_logger()

MODEL_DIR = Path(__file__).parent.parent / "models"


def load_active_model(worker_type: str):
    """Load the most-recent trained model for *worker_type*.

    Looks for files matching ``matching_{worker_type}_*.pkl`` first, then
    ``matching_all_*.pkl`` as a fallback.  Returns ``None`` if no model file
    is found so the caller can fall back to cosine similarity alone.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    patterns = [
        f"matching_{worker_type}_*.pkl",
        "matching_all_*.pkl",
    ]
    for pattern in patterns:
        candidates = sorted(MODEL_DIR.glob(pattern), reverse=True)
        if candidates:
            try:
                with open(candidates[0], "rb") as fh:
                    model = pickle.load(fh)  # noqa: S301
                logger.info(
                    "model_loaded",
                    path=str(candidates[0]),
                    worker_type=worker_type,
                )
                return model
            except Exception as exc:
                logger.warning(
                    "model_load_failed",
                    path=str(candidates[0]),
                    error=str(exc),
                )
    logger.info(
        "no_model_found",
        worker_type=worker_type,
        fallback="cosine_sim_only",
    )
    return None


def load_model_metrics() -> dict:
    """Carga el archivo de métricas más reciente de cada worker_type."""
    import json

    metrics: dict[str, dict] = {}
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(MODEL_DIR.glob("metrics_*.json"), reverse=True):
        stem = path.stem  # metrics_<worker_type>_<version>
        parts = stem.split("_", 2)
        if len(parts) >= 2:
            wtype = parts[1]
            if wtype not in metrics:
                try:
                    with open(path) as fh:
                        metrics[wtype] = json.load(fh)
                except Exception:
                    pass
    if not metrics:
        raise FileNotFoundError("No metrics files found in model dir.")
    return metrics
