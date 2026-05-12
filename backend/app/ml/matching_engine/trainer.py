# RF: RF086-RF095 — Supervised model trainer for the matching engine
import json
import pickle
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import structlog
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.matching_engine.dataset_builder import build_training_dataset
from app.ml.matching_engine.drift_detector import save_reference_scores
from app.ml.matching_engine.features import FEATURE_NAMES  # noqa: F401 — re-exported

logger = structlog.get_logger()

MODEL_DIR = Path(__file__).parent.parent / "models"

# Thresholds per CLAUDE.md — do not change without F1 validation
F1_MINIMUM = 0.75
F1_ALERT = 0.70


def train_matching_model(
    X: np.ndarray,  # noqa: N803
    y: np.ndarray,
    worker_type: str = "all",
    deploy_if_better: bool = True,
) -> dict:
    """Train the supervised matching model.

    Args:
        X: Feature matrix with shape (n_samples, 9).
        y: Binary labels — 1 = accepted application, 0 = rejected.
        worker_type: One of primer_empleo | experiencia | oficio | all.
        deploy_if_better: Persist to disk if F1 >= F1_MINIMUM.

    Returns:
        dict with keys: deployed (bool), metrics (dict), and optionally
        model_path and version.
    """
    if len(X) < 10:
        logger.warning("insufficient_training_data", n_samples=len(X))
        return {"deployed": False, "metrics": {}, "reason": "insufficient_data"}

    stratify = y if len(np.unique(y)) > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(  # noqa: N806
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=4,
                    learning_rate=0.1,
                    random_state=42,  # reproducibility per CLAUDE.md
                    subsample=0.8,
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    metrics = {
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
    }
    logger.info("model_trained", worker_type=worker_type, **metrics)

    if metrics["f1"] < F1_ALERT:
        logger.error(
            "model_f1_below_alert_threshold",
            f1=metrics["f1"],
            threshold=F1_ALERT,
        )

    if metrics["f1"] < F1_MINIMUM:
        logger.warning(
            "model_f1_below_minimum",
            f1=metrics["f1"],
            threshold=F1_MINIMUM,
        )
        return {"deployed": False, "metrics": metrics}

    if deploy_if_better:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        version_tag = (
            f"v{datetime.now(UTC).strftime('%Y%m%d%H%M')}-{worker_type}"
        )
        model_path = MODEL_DIR / f"matching_{worker_type}_{version_tag}.pkl"
        with open(model_path, "wb") as fh:
            pickle.dump(pipeline, fh)
        logger.info(
            "model_deployed",
            path=str(model_path),
            version=version_tag,
        )
        return {
            "deployed": True,
            "metrics": metrics,
            "model_path": str(model_path),
            "version": version_tag,
        }

    return {"deployed": False, "metrics": metrics}


async def train_from_db(
    db,
    worker_type: str = "all",
    deploy_if_better: bool = True,
) -> dict:
    """Construye el dataset desde match_events y entrena el modelo supervisado.

    Persiste también un archivo de métricas JSON y los scores de referencia
    para la detección de drift PSI posterior.
    """
    X, y = await build_training_dataset(db, worker_type=worker_type)
    if len(X) == 0:
        return {"deployed": False, "metrics": {}, "reason": "insufficient_data"}

    result = train_matching_model(X, y, worker_type=worker_type, deploy_if_better=deploy_if_better)

    if result.get("deployed") and result.get("metrics"):
        version_tag = result.get("version", "unknown")
        metrics_path = MODEL_DIR / f"metrics_{worker_type}_{version_tag}.json"
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with open(metrics_path, "w") as fh:
            json.dump(result["metrics"], fh)

        model_path = result.get("model_path")
        if model_path:
            try:
                with open(model_path, "rb") as fh:
                    pipeline = pickle.load(fh)  # noqa: S301
                scores = pipeline.predict_proba(X)[:, 1]
                save_reference_scores(scores, worker_type)
            except Exception as exc:
                logger.warning("reference_scores_save_failed", error=str(exc))

    return result
