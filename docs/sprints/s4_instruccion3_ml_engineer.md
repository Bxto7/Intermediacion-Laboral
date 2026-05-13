# SPRINT 4 — INSTRUCCIÓN 3 de 5
# Agente: `ml-engineer`
# Skills a cargar: `skills/nlp-embeddings`, `skills/database-architect`
# Tarea: DatasetBuilder real + Pipeline sklearn completo + PSI drift detection + métricas producción

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
Las instrucciones 1–2 del Sprint 4 entregaron seguridad hardened y el panel admin con KPIs.

**Tu trabajo:** Construir el pipeline de entrenamiento ML con datos reales de la BD,
implementar detección de drift con PSI, y exponer métricas de salud del modelo.

**RF que implementas:** RF086–RF095 (M05 avanzado), RF151–RF155 (M10 drift/equidad)

---

## PARTE A — DatasetBuilder desde datos reales de BD

Crea `app/ml/matching_engine/dataset_builder.py`:

```python
# app/ml/matching_engine/dataset_builder.py
"""
Construcción del dataset de entrenamiento desde datos reales de la BD.
Usa match_events como feedback implícito de relevancia.
Cubre RF086–RF090 (M05).
"""
from uuid import UUID
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.ml.matching_engine.features import build_feature_vector, FEATURE_NAMES

logger = structlog.get_logger()

MIN_SAMPLES_TO_TRAIN = 100  # mínimo de eventos para entrenar
POSITIVE_ACTIONS = {"applied", "contacted"}     # label=1
NEGATIVE_ACTIONS = {"dismissed"}                # label=0
# "viewed" sin acción posterior → negativo después de 48h


async def build_training_dataset(
    db: AsyncSession,
    worker_type: str | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Construye X (features) e y (labels) desde match_events + job_offers + workers.
    
    Label positivo (y=1): el trabajador postuló o contactó al empleador.
    Label negativo (y=0): el trabajador descartó la oferta (o la vio sin acción).
    
    Si worker_type es None → incluye todos los tipos.
    """
    type_filter = "AND me.worker_type = :worker_type" if worker_type else ""
    
    query = text(f"""
        SELECT
            me.worker_id,
            me.matched_job_id,
            me.cosine_sim,
            me.combined_score,
            me.action,
            me.worker_type,
            w.years_experience,
            w.avg_rating,
            w.district        AS worker_district,
            w.trade_category,
            w.skills          AS worker_skills,
            jo.district       AS offer_district,
            jo.required_skills AS offer_skills,
            jo.years_required,
            jo.salary_min,
            jo.salary_max,
            jo.published_at
        FROM match_events me
        JOIN workers w ON me.worker_id = w.id
        LEFT JOIN job_offers jo ON me.matched_job_id = jo.id
        WHERE me.action IN ('applied', 'contacted', 'dismissed')
          AND me.matched_job_id IS NOT NULL
          {type_filter}
        ORDER BY me.created_at DESC
        LIMIT 10000
    """)
    
    params = {"worker_type": worker_type} if worker_type else {}
    result = await db.execute(query, params)
    rows = result.fetchall()

    if len(rows) < MIN_SAMPLES_TO_TRAIN:
        logger.warning(
            "insufficient_training_data",
            samples=len(rows),
            minimum=MIN_SAMPLES_TO_TRAIN,
            worker_type=worker_type,
        )
        return np.array([]), np.array([])

    X_list, y_list = [], []
    
    for row in rows:
        # Label
        label = 1 if row.action in POSITIVE_ACTIONS else 0

        # Calcular skill_overlap
        worker_skills = set(row.worker_skills or [])
        offer_skills  = set(row.offer_skills or [])
        skill_overlap = len(worker_skills & offer_skills) / max(len(worker_skills | offer_skills), 1)

        # Construir objeto mínimo para build_feature_vector
        class _W:
            worker_type = row.worker_type
            district = row.worker_district
            years_experience = row.years_experience or 0
            avg_rating = float(row.avg_rating or 0)
            expected_salary = None
            skills = list(worker_skills)
            portfolio_count = 0  # no disponible directamente aquí

        class _O:
            district = row.offer_district
            required_skills = list(offer_skills)
            years_required = row.years_required or 0
            salary_min = row.salary_min
            salary_max = row.salary_max

        from app.core.types import WorkerType
        try:
            wt = WorkerType(row.worker_type)
        except ValueError:
            continue

        fv = build_feature_vector(
            worker=_W(),
            offer=_O(),
            cosine_sim=float(row.cosine_sim or 0),
            skill_overlap=skill_overlap,
        )
        X_list.append(fv)
        y_list.append(label)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)

    logger.info(
        "dataset_built",
        worker_type=worker_type or "all",
        samples=len(X),
        positive_rate=float(y.mean()) if len(y) > 0 else 0,
    )
    return X, y
```

---

## PARTE B — Pipeline sklearn con StandardScaler + GradientBoosting

Actualiza `app/ml/matching_engine/trainer.py` para usar el DatasetBuilder:

```python
# app/ml/matching_engine/trainer.py — reemplazar la función principal

async def train_from_db(
    db: AsyncSession,
    worker_type: str | None = None,
    deploy_if_better: bool = True,
) -> dict:
    """
    Entrena el modelo directamente desde datos reales de la BD.
    Llama al DatasetBuilder y luego al pipeline de entrenamiento.
    """
    from app.ml.matching_engine.dataset_builder import build_training_dataset

    X, y = await build_training_dataset(db, worker_type=worker_type)

    if len(X) == 0:
        return {"deployed": False, "reason": "insufficient_data"}

    return train_matching_model(X, y, worker_type=worker_type or "all", deploy_if_better=deploy_if_better)
```

**Verificar que el pipeline siempre sigue este orden:**
```python
Pipeline([
    ("scaler", StandardScaler()),
    ("clf", GradientBoostingClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,    # ✅ SIEMPRE random_state=42
        subsample=0.8,
    ))
])
```

---

## PARTE C — PSI (Population Stability Index) para drift detection

Crea `app/ml/matching_engine/drift_detector.py`:

```python
# app/ml/matching_engine/drift_detector.py
"""
Detección de drift del modelo usando PSI (Population Stability Index).
PSI > 0.25 → drift significativo → alerta + reentrenamiento automático.
Cubre RF151–RF155 (M10).
"""
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

PSI_THRESHOLD_WARN  = 0.10   # drift leve
PSI_THRESHOLD_ALERT = 0.25   # drift significativo → reentrenar


def calculate_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    buckets: int = 10,
) -> float:
    """
    Calcula el PSI entre la distribución de scores esperada (entrenamiento)
    y la actual (producción).
    PSI < 0.10: sin drift
    PSI 0.10–0.25: drift leve — monitorear
    PSI > 0.25: drift significativo — reentrenar
    """
    # Crear buckets sobre la distribución esperada
    breakpoints = np.percentile(expected, np.linspace(0, 100, buckets + 1))
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf

    expected_counts = np.histogram(expected, bins=breakpoints)[0]
    actual_counts   = np.histogram(actual,   bins=breakpoints)[0]

    # Evitar divisiones por cero
    expected_pct = np.clip(expected_counts / max(len(expected), 1), 1e-6, None)
    actual_pct   = np.clip(actual_counts   / max(len(actual),   1), 1e-6, None)

    psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(psi)


async def detect_score_drift(
    db: AsyncSession,
    worker_type: str,
    lookback_days_reference: int = 30,
    lookback_days_current:   int = 7,
) -> dict:
    """
    Compara la distribución de combined_score en el período de referencia
    vs el período actual.
    Si PSI > 0.25 → log de alerta para reentrenamiento.
    """
    query = text("""
        SELECT
            combined_score,
            created_at
        FROM match_events
        WHERE worker_type = :worker_type
          AND combined_score IS NOT NULL
          AND created_at >= NOW() - INTERVAL ':lookback days'
        ORDER BY created_at DESC
    """)

    # Período de referencia (30 días)
    ref_result = await db.execute(text("""
        SELECT combined_score FROM match_events
        WHERE worker_type = :wt
          AND combined_score IS NOT NULL
          AND created_at BETWEEN NOW() - INTERVAL '30 days' AND NOW() - INTERVAL '7 days'
    """), {"wt": worker_type})
    ref_scores = np.array([r[0] for r in ref_result.fetchall()], dtype=np.float32)

    # Período actual (7 días)
    curr_result = await db.execute(text("""
        SELECT combined_score FROM match_events
        WHERE worker_type = :wt
          AND combined_score IS NOT NULL
          AND created_at >= NOW() - INTERVAL '7 days'
    """), {"wt": worker_type})
    curr_scores = np.array([r[0] for r in curr_result.fetchall()], dtype=np.float32)

    if len(ref_scores) < 10 or len(curr_scores) < 10:
        return {"psi": None, "status": "insufficient_data", "worker_type": worker_type}

    psi = calculate_psi(ref_scores, curr_scores)

    status = "ok"
    if psi > PSI_THRESHOLD_ALERT:
        status = "drift_alert"
        logger.error(
            "model_drift_significant",
            worker_type=worker_type,
            psi=psi,
            action="RETRAINING_REQUIRED",
        )
    elif psi > PSI_THRESHOLD_WARN:
        status = "drift_warning"
        logger.warning("model_drift_warning", worker_type=worker_type, psi=psi)
    else:
        logger.info("model_no_drift", worker_type=worker_type, psi=psi)

    return {
        "worker_type": worker_type,
        "psi": round(psi, 4),
        "status": status,
        "ref_samples": len(ref_scores),
        "curr_samples": len(curr_scores),
    }


async def check_all_types_drift(db: AsyncSession) -> list[dict]:
    """Verificar drift para los 3 tipos de usuario. Llamado por Celery Beat."""
    results = []
    for wtype in ["primer_empleo", "experiencia", "oficio"]:
        result = await detect_score_drift(db, worker_type=wtype)
        results.append(result)
        # Si hay drift significativo → encolar reentrenamiento
        if result.get("status") == "drift_alert":
            from app.tasks.ml_tasks import retrain_model_task
            retrain_model_task.delay(wtype)
    return results
```

---

## PARTE D — Tarea Celery de reentrenamiento automático

Crea `app/tasks/ml_tasks.py`:

```python
# app/tasks/ml_tasks.py
"""Tareas Celery para el pipeline ML: reentrenamiento y drift detection."""
import uuid as uuid_mod
import asyncio
from celery import shared_task
import structlog

logger = structlog.get_logger()


@shared_task(name="tasks.retrain_model_if_needed")
def retrain_model_if_needed_task():
    """
    Tarea semanal (Celery Beat): verificar drift y reentrenar si es necesario.
    """
    asyncio.run(_retrain_all())


async def _retrain_all():
    from app.core.db import AsyncSessionFactory
    from app.ml.matching_engine.drift_detector import check_all_types_drift
    from app.ml.matching_engine.trainer import train_from_db

    async with AsyncSessionFactory() as db:
        drift_results = await check_all_types_drift(db)
        for result in drift_results:
            if result.get("status") == "drift_alert":
                await train_from_db(db, worker_type=result["worker_type"], deploy_if_better=True)


@shared_task(name="tasks.retrain_model")
def retrain_model_task(worker_type: str):
    """Reentrenar modelo para un tipo específico (disparado por drift alert)."""
    asyncio.run(_retrain_single(worker_type))


async def _retrain_single(worker_type: str):
    from app.core.db import AsyncSessionFactory
    from app.ml.matching_engine.trainer import train_from_db

    async with AsyncSessionFactory() as db:
        result = await train_from_db(db, worker_type=worker_type, deploy_if_better=True)
        logger.info("model_retrained", worker_type=worker_type, result=result)
```

---

## PARTE E — Endpoint de métricas del modelo (protegido ADMIN)

Actualiza `app/api/v1/admin/dashboard.py` para incluir drift:

```python
# Agregar al router de admin:
@router.get("/model/drift")
async def get_drift_status(db: AsyncSession = Depends(get_db)):
    """PSI drift status para los 3 tipos. Solo ADMIN."""
    from app.ml.matching_engine.drift_detector import check_all_types_drift
    return await check_all_types_drift(db)
```

---

## TESTS OBLIGATORIOS

```bash
touch tests/unit/test_dataset_builder.py
touch tests/unit/test_psi_drift_detector.py
touch tests/unit/test_ml_pipeline.py
```

**`tests/unit/test_psi_drift_detector.py`** debe cubrir:
- `calculate_psi(A, A)` ≈ 0 (misma distribución → sin drift)
- `calculate_psi(uniform, muy_sesgado)` > 0.25 (drift significativo)
- Con < 10 muestras → retorna `"insufficient_data"`
- PSI > 0.25 → log de `ERROR` (verificar con caplog)

**`tests/unit/test_ml_pipeline.py`** debe cubrir:
- `Pipeline` contiene `StandardScaler` como primer paso
- `GradientBoostingClassifier` tiene `random_state=42`
- F1 < 0.70 → log de ERROR en trainer
- F1 ≥ 0.75 → `deployed=True`

**`tests/unit/test_dataset_builder.py`** debe cubrir:
- Con < 100 muestras → retorna arrays vacíos
- Cada feature vector tiene shape (9,)
- Labels solo contienen 0 y 1

```bash
pytest tests/unit/test_psi_drift_detector.py tests/unit/test_ml_pipeline.py \
       tests/unit/test_dataset_builder.py -v
ruff check app/ml/matching_engine/
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

- `app/ml/matching_engine/dataset_builder.py` — DatasetBuilder desde BD real
- `app/ml/matching_engine/drift_detector.py` — PSI con 3 niveles de alerta
- `app/ml/matching_engine/trainer.py` — actualizado con `train_from_db()`
- `app/tasks/ml_tasks.py` — reentrenamiento automático por Celery
- `app/api/v1/admin/dashboard.py` — endpoint drift (actualizado)
- Tests unitarios

---

**Cuando termines, el agente `senior-frontend` con skill `ui-ux-pro-max` recibirá la instrucción 4
para implementar el frontend completo: Onboarding, Wizard, Dashboard por tipo y Panel Admin.**
