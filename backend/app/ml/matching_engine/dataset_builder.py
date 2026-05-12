# RF: RF086-RF095 (M05) — Construcción de dataset de entrenamiento desde match_events
from __future__ import annotations

import numpy as np
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# Mínimo de eventos para considerar el dataset válido para entrenamiento
MIN_SAMPLES = 50


async def build_training_dataset(
    db: AsyncSession,
    worker_type: str = "all",
) -> tuple[np.ndarray, np.ndarray]:
    """Construye (X, y) desde match_events para el modelo supervisado.

    Columnas de features (alineadas con FEATURE_NAMES en features.py):
        cosine_sim, ml_score, reputation_score, combined_score,
        rank_position_norm, is_oficio, is_primer_empleo, is_experiencia,
        equity_flag

    Label y: 1 si action == 'accepted' (postulación exitosa), 0 si 'rejected'.
    Eventos sin action definida se excluyen.
    """
    where_type = "" if worker_type == "all" else "AND worker_type = :wtype"

    sql = text(f"""
        SELECT
            COALESCE(cosine_sim, 0)        AS cosine_sim,
            COALESCE(ml_score, 0)          AS ml_score,
            COALESCE(reputation_score, 0)  AS reputation_score,
            COALESCE(combined_score, 0)    AS combined_score,
            COALESCE(rank_position, 50)    AS rank_position,
            worker_type,
            equity_flag,
            action
        FROM match_events
        WHERE action IN ('accepted', 'rejected')
        {where_type}
        ORDER BY created_at DESC
        LIMIT 50000
    """)

    params = {} if worker_type == "all" else {"wtype": worker_type}
    rows = (await db.execute(sql, params)).fetchall()

    if len(rows) < MIN_SAMPLES:
        logger.warning(
            "dataset_too_small",
            n_rows=len(rows),
            worker_type=worker_type,
            min_required=MIN_SAMPLES,
        )
        return np.empty((0, 9)), np.empty(0)

    X_list, y_list = [], []
    for r in rows:
        rank_norm = min(float(r.rank_position) / 50.0, 1.0)
        is_oficio = 1.0 if r.worker_type == "oficio" else 0.0
        is_primer = 1.0 if r.worker_type == "primer_empleo" else 0.0
        is_exp = 1.0 if r.worker_type == "experiencia" else 0.0
        equity = 1.0 if r.equity_flag else 0.0

        X_list.append([
            float(r.cosine_sim),
            float(r.ml_score),
            float(r.reputation_score),
            float(r.combined_score),
            rank_norm,
            is_oficio,
            is_primer,
            is_exp,
            equity,
        ])
        y_list.append(1 if r.action == "accepted" else 0)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)

    logger.info(
        "dataset_built",
        n_samples=len(y),
        positive_rate=round(float(y.mean()), 3),
        worker_type=worker_type,
    )
    return X, y
