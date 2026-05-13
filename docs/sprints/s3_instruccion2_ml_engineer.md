# SPRINT 3 — INSTRUCCIÓN 2 de 5
# Agente: `ml-engineer`
# Skills a cargar: `skills/nlp-embeddings`, `skills/database-architect`
# Tarea: Implementar Motor de Matching ML diferenciado (M05 / RF076–RF095) + Equidad (M10 / RF146–RF155)

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
La instrucción 1 del Sprint 3 (security-auditor) ya creó la tabla `match_events` con migración
aplicada. Construyes sobre esa base.

**Tu trabajo:** Implementar el motor ML de emparejamiento supervisado completo, diferenciado
por los tres tipos de usuario (PRIMER_EMPLEO / EXPERIENCIA / OFICIO), con re-ranking equitativo,
explainer de recomendaciones y cold-start robusto.

**RF que implementas:** RF076–RF095 (M05), RF146–RF155 (M10), RF096–RF105 (cold-start M06 parcial)

---

## PASO 1 — Migraciones de BD (ejecutar primero con Bash)

```bash
alembic revision --autogenerate -m "add ml matching tables sprint3"
alembic upgrade head
```

**Tablas nuevas requeridas:**

```sql
-- Versiones del modelo ML — trazabilidad de entrenamiento
CREATE TABLE model_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_tag     VARCHAR(50) NOT NULL UNIQUE,   -- ej: "v1.0.0-20260515"
    worker_type     VARCHAR(20),                   -- NULL = aplica a todos
    algorithm       VARCHAR(100) NOT NULL,         -- "GradientBoostingClassifier"
    f1_score        DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall_score    DECIMAL(5,4),
    feature_names   JSONB DEFAULT '[]',
    is_active       BOOLEAN DEFAULT false,
    trained_at      TIMESTAMPTZ DEFAULT now(),
    deployed_at     TIMESTAMPTZ
);

-- Registro de auditoría de equidad
CREATE TABLE equity_audit_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id           UUID NOT NULL REFERENCES workers(id),
    worker_type         VARCHAR(20) NOT NULL,
    gender              VARCHAR(10),               -- 'm', 'f', 'otro', NULL si no informado
    district            VARCHAR(50),
    disparate_impact    DECIMAL(5,4),              -- ratio calculado
    reranking_applied   BOOLEAN DEFAULT false,
    original_rank       INTEGER,
    adjusted_rank       INTEGER,
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- Encuestas económicas para KPI Reducción Brecha Salarial
CREATE TABLE economic_surveys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id       UUID NOT NULL REFERENCES workers(id),
    survey_phase    VARCHAR(10) NOT NULL,          -- 'pre', 'post'
    monthly_income  BYTEA NOT NULL,               -- AES-256 cifrado (Ley 29733)
    employment_type VARCHAR(30),                   -- 'formal', 'informal', 'desempleado'
    consent_given   BOOLEAN NOT NULL DEFAULT false, -- Ley 29733 obligatorio
    surveyed_at     TIMESTAMPTZ DEFAULT now()
);
```

---

## PASO 2 — Feature engineering diferenciado por tipo

Crea `app/ml/matching_engine/features.py`:

```python
# app/ml/matching_engine/features.py
"""
Feature engineering para el motor de matching supervisado.
Diferencia los features según worker_type como define el CLAUDE.md.
"""
from dataclasses import dataclass
from uuid import UUID
import numpy as np
from app.models import Worker, JobOffer, MatchEvent
from app.core.types import WorkerType


@dataclass
class MatchFeatureVector:
    cosine_sim: float           # similitud semántica pgvector
    skill_overlap: float        # Jaccard entre skills del perfil y la oferta
    district_match: float       # 1.0 si mismo distrito, 0.5 si Junín, 0.0 fuera
    experience_gap: float       # |años_requeridos - años_trabajador| normalizado
    salary_fit: float           # 0-1 según rango salarial compatible (0 si no hay datos)
    reputation: float           # avg_rating / 5.0 (0 para PRIMER_EMPLEO)
    recency_boost: float        # boost si oferta publicada < 7 días
    portfolio_size: float       # len(portfolio_entries) / 20.0 solo OFICIO, 0 resto
    worker_type_encoded: float  # 0=primer_empleo, 0.5=experiencia, 1.0=oficio


def build_feature_vector(
    worker: Worker,
    offer: JobOffer,
    cosine_sim: float,
    skill_overlap: float,
) -> np.ndarray:
    """
    Construye el vector de features para el clasificador supervisado.
    Los pesos internos del combined_score siguen la fórmula del CLAUDE.md.
    """
    type_encoding = {
        WorkerType.PRIMER_EMPLEO: 0.0,
        WorkerType.EXPERIENCIA: 0.5,
        WorkerType.OFICIO: 1.0,
    }
    
    # district_match
    if worker.district == offer.district:
        district_match = 1.0
    elif offer.district in ["Huancayo", "El Tambo", "Chilca"]:
        district_match = 0.5
    else:
        district_match = 0.0
    
    # salary_fit — solo si ambos tienen datos
    if worker.expected_salary and offer.salary_min and offer.salary_max:
        if offer.salary_min <= worker.expected_salary <= offer.salary_max:
            salary_fit = 1.0
        elif worker.expected_salary < offer.salary_min:
            salary_fit = max(0.0, 1.0 - (offer.salary_min - worker.expected_salary) / offer.salary_min)
        else:
            salary_fit = 0.5
    else:
        salary_fit = 0.0
    
    # portfolio_size solo OFICIO
    portfolio_size = 0.0
    if worker.worker_type == WorkerType.OFICIO and hasattr(worker, 'portfolio_count'):
        portfolio_size = min(worker.portfolio_count / 20.0, 1.0)
    
    features = MatchFeatureVector(
        cosine_sim=cosine_sim,
        skill_overlap=skill_overlap,
        district_match=district_match,
        experience_gap=min(abs((offer.years_required or 0) - worker.years_experience) / 10.0, 1.0),
        salary_fit=salary_fit,
        reputation=worker.avg_rating / 5.0 if worker.worker_type != WorkerType.PRIMER_EMPLEO else 0.0,
        recency_boost=0.0,  # calcular en el llamador
        portfolio_size=portfolio_size,
        worker_type_encoded=type_encoding[worker.worker_type],
    )
    
    return np.array([
        features.cosine_sim,
        features.skill_overlap,
        features.district_match,
        features.experience_gap,
        features.salary_fit,
        features.reputation,
        features.recency_boost,
        features.portfolio_size,
        features.worker_type_encoded,
    ], dtype=np.float32)


FEATURE_NAMES = [
    "cosine_sim", "skill_overlap", "district_match", "experience_gap",
    "salary_fit", "reputation", "recency_boost", "portfolio_size", "worker_type_encoded"
]
```

---

## PASO 3 — combined_score exacto según CLAUDE.md

Crea `app/ml/matching_engine/scorer.py`:

```python
# app/ml/matching_engine/scorer.py
"""
Score combinado — fórmula FIJA del CLAUDE.md. No modificar pesos sin validación F1.
"""
from app.core.types import WorkerType


# ✅ Pesos exactos del CLAUDE.md — NO CAMBIAR
SCORE_WEIGHTS = {
    WorkerType.PRIMER_EMPLEO: (0.65, 0.35, 0.00),  # cosine, ml, reputation
    WorkerType.EXPERIENCIA:   (0.50, 0.30, 0.20),
    WorkerType.OFICIO:        (0.45, 0.25, 0.30),
}


def combined_score(
    cosine_sim: float,
    ml_score: float,
    reputation: float,
    worker_type: WorkerType,
) -> float:
    """
    Fórmula fija de combined_score del CLAUDE.md.
    reputation debe estar en escala 0-5; se normaliza internamente a 0-1.
    """
    alpha, beta, gamma = SCORE_WEIGHTS[worker_type]
    return alpha * cosine_sim + beta * ml_score + gamma * (reputation / 5.0)
```

---

## PASO 4 — Motor de matching principal

Crea `app/ml/matching_engine/engine.py`:

```python
# app/ml/matching_engine/engine.py
"""
Motor de matching diferenciado por WorkerType.
Cubre RF076–RF095 (M05) del subcapítulo 4.3.2.
"""
import uuid
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import structlog

from app.models import Worker, JobOffer, MatchEvent
from app.core.types import WorkerType
from app.ml.matching_engine.scorer import combined_score, SCORE_WEIGHTS
from app.ml.matching_engine.features import build_feature_vector, FEATURE_NAMES
from app.ml.equity_ranker.ranker import apply_equity_reranking
from app.ml.explainer.explainer import build_match_explanation
from app.ml.cold_start.resolver import resolve_cold_start
from app.schemas.matching import JobMatchResult

logger = structlog.get_logger()

TOP_K_VECTOR_SEARCH = 50   # Candidatos del vector search antes del re-ranking
TOP_K_FINAL = 20           # Resultados finales retornados


async def match_worker_to_jobs(
    worker_id: UUID,
    db: AsyncSession,
    top_k: int = TOP_K_FINAL,
) -> list[JobMatchResult]:
    """
    Pipeline completo de matching (RF076–RF090):
    1. Verificar que el worker tiene embedding (cold-start si no)
    2. Vector search cosine en pgvector → top-50 candidatos
    3. Re-ranking con modelo supervisado GradientBoosting
    4. Aplicar combined_score con pesos por worker_type
    5. Filtro equitativo (disparate impact ≥ 0.80)
    6. Construir explicaciones de matching
    7. Registrar en match_events (auditoría)
    8. Retornar top-K con explicaciones
    """
    # Cargar worker
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise ValueError(f"Worker {worker_id} no encontrado")

    worker_type = WorkerType(worker.worker_type)

    # Cold-start: generar embedding si no existe
    if worker.embedding is None:
        logger.info("cold_start_triggered", worker_id=str(worker_id), worker_type=worker.worker_type)
        worker = await resolve_cold_start(worker, db)
        if worker.embedding is None:
            logger.warning("cold_start_failed_no_embedding", worker_id=str(worker_id))
            return []

    # Vector search — cosine similarity con pgvector
    vector_query = text("""
        SELECT
            jo.id,
            jo.title,
            jo.employer_id,
            jo.district,
            jo.required_skills,
            jo.years_required,
            jo.salary_min,
            jo.salary_max,
            jo.published_at,
            1 - (jo.embedding <=> :worker_embedding::vector) AS cosine_sim
        FROM job_offers jo
        WHERE jo.is_active = true
          AND jo.embedding IS NOT NULL
        ORDER BY jo.embedding <=> :worker_embedding::vector
        LIMIT :limit
    """)
    
    candidates = (await db.execute(
        vector_query,
        {"worker_embedding": str(worker.embedding), "limit": TOP_K_VECTOR_SEARCH}
    )).fetchall()

    if not candidates:
        return []

    # Cargar modelo supervisado y calcular ml_score
    from app.ml.matching_engine.model_loader import load_active_model
    model = load_active_model(worker_type)

    scored_results = []
    for row in candidates:
        # Jaccard de skills
        offer_skills = set(row.required_skills or [])
        worker_skills = set(worker.skills or [])
        skill_overlap = len(offer_skills & worker_skills) / max(len(offer_skills | worker_skills), 1)

        # Feature vector para el clasificador
        offer = JobOffer(**dict(row))
        fv = build_feature_vector(worker, offer, float(row.cosine_sim), skill_overlap)

        # ml_score del clasificador supervisado
        ml_score = float(model.predict_proba([fv])[0][1]) if model else float(row.cosine_sim)

        # combined_score con pesos del CLAUDE.md
        score = combined_score(
            cosine_sim=float(row.cosine_sim),
            ml_score=ml_score,
            reputation=float(worker.avg_rating or 0),
            worker_type=worker_type,
        )

        scored_results.append({
            "job_id": row.id,
            "cosine_sim": float(row.cosine_sim),
            "ml_score": ml_score,
            "combined_score": score,
            "offer_row": row,
            "skill_overlap": skill_overlap,
        })

    # Ordenar por combined_score
    scored_results.sort(key=lambda x: x["combined_score"], reverse=True)

    # Re-ranking equitativo (RF146–RF155)
    scored_results = await apply_equity_reranking(scored_results, worker, db)

    # Construir respuesta con explicaciones (M10 / RF146–RF150)
    final_results = []
    for i, item in enumerate(scored_results[:top_k]):
        explanation = build_match_explanation(
            worker=worker,
            offer_row=item["offer_row"],
            cosine_sim=item["cosine_sim"],
            skill_overlap=item["skill_overlap"],
            worker_type=worker_type,
        )
        final_results.append(JobMatchResult(
            job_id=item["job_id"],
            combined_score=item["combined_score"],
            rank=i + 1,
            explanation=explanation,
        ))

    # Registrar en match_events (auditoría)
    await _log_match_events(worker, final_results, db)

    logger.info(
        "matching_completed",
        worker_id=str(worker_id),
        worker_type=worker.worker_type,
        results_count=len(final_results),
    )
    return final_results


async def _log_match_events(worker: Worker, results: list[JobMatchResult], db: AsyncSession):
    """Registrar eventos de matching en la tabla de auditoría."""
    for result in results:
        event = MatchEvent(
            id=uuid.uuid4(),
            worker_id=worker.id,
            worker_type=worker.worker_type,
            matched_job_id=result.job_id,
            combined_score=result.combined_score,
            rank_position=result.rank,
            action="viewed",
        )
        db.add(event)
    await db.commit()
```

---

## PASO 5 — Cold-start diferenciado por tipo

Crea `app/ml/cold_start/resolver.py`:

```python
# app/ml/cold_start/resolver.py
"""
Resolución de cold-start (RF096–RF105).
Estrategia: construir embedding desde contenido del perfil, NO desde clicks.
Diferenciado por WorkerType.
"""
from app.core.types import WorkerType
from app.nlp.embeddings import generate_embedding_sync
from app.models import Worker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import WizardProgress, PortfolioEntry
import structlog

logger = structlog.get_logger()


async def resolve_cold_start(worker: Worker, db: AsyncSession) -> Worker:
    """
    Genera embedding inicial para un worker sin historial.
    PRIMER_EMPLEO: desde respuestas del wizard
    OFICIO: desde entradas del portfolio (si existen) o metadata del oficio
    EXPERIENCIA: desde campos del perfil manual
    """
    worker_type = WorkerType(worker.worker_type)
    profile_text = None

    if worker_type == WorkerType.PRIMER_EMPLEO:
        # Cargar respuestas del wizard
        res = await db.execute(
            select(WizardProgress).where(WizardProgress.worker_id == worker.id)
        )
        progress = res.scalar_one_or_none()
        if progress and progress.extracted_skills:
            skills = progress.extracted_skills
            interests = progress.answers.get("job_interests", "")
            profile_text = (
                f"primer empleo | {worker.district} | "
                f"habilidades: {', '.join(skills)} | "
                f"intereses: {interests}"
            )
        else:
            # Mínimo viable si el wizard no tiene respuestas aún
            profile_text = f"primer empleo | {worker.district} | sin experiencia previa"

    elif worker_type == WorkerType.OFICIO:
        # Cargar entradas del portfolio
        res = await db.execute(
            select(PortfolioEntry).where(PortfolioEntry.worker_id == worker.id)
        )
        entries = res.scalars().all()
        if entries:
            all_skills = []
            for entry in entries:
                all_skills.extend(entry.extracted_skills or [])
            unique_skills = list(set(all_skills))
            profile_text = (
                f"{worker.trade_category} | {worker.years_experience} años | "
                f"{worker.district} | trabajos: {len(entries)} | "
                f"habilidades: {', '.join(unique_skills)}"
            )
        else:
            # Solo metadata del oficio
            profile_text = (
                f"{worker.trade_category} | {worker.district} | "
                f"{worker.years_experience} años de experiencia en oficio"
            )

    else:  # EXPERIENCIA
        # Desde campos del perfil
        profile_text = (
            f"{getattr(worker, 'job_title', '')} | "
            f"{worker.years_experience} años | "
            f"{worker.district}"
        )

    if profile_text:
        embedding = generate_embedding_sync(profile_text)
        worker.embedding = embedding
        db.add(worker)
        await db.commit()
        logger.info(
            "cold_start_embedding_generated",
            worker_id=str(worker.id),
            worker_type=worker.worker_type,
        )

    return worker
```

---

## PASO 6 — Equity Re-ranker (RF146–RF155)

Crea `app/ml/equity_ranker/ranker.py`:

```python
# app/ml/equity_ranker/ranker.py
"""
Re-ranking equitativo por género y zona geográfica.
Disparate Impact Ratio mínimo: 0.80 (CLAUDE.md).
Cubre RF146–RF155 (M10).
"""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Worker, EquityAuditLog
import uuid

logger = structlog.get_logger()

DISPARATE_IMPACT_THRESHOLD = 0.80


async def apply_equity_reranking(
    scored_results: list[dict],
    worker: Worker,
    db: AsyncSession,
) -> list[dict]:
    """
    Verifica si el ranking actual tiene disparate impact < 0.80
    por distrito (zona rural vs urbana Huancayo).
    Si disparate impact < umbral → aplica ajuste de posición.
    Registra en equity_audit_logs.
    """
    # Calcular PSI (Population Stability Index) simple por distrito
    # Para el proyecto: ratio de workers de El Tambo/Chilca vs Huancayo en top-10
    districts_top10 = [
        r["offer_row"].district for r in scored_results[:10]
        if r["offer_row"].district
    ]
    
    if not districts_top10:
        return scored_results

    huancayo_count = districts_top10.count("Huancayo")
    other_count = len(districts_top10) - huancayo_count

    # Disparate impact: ratio de oportunidades fuera de Huancayo central
    if huancayo_count > 0:
        disparate_impact = other_count / huancayo_count
    else:
        disparate_impact = 1.0

    reranking_applied = False
    
    if disparate_impact < DISPARATE_IMPACT_THRESHOLD:
        # Boost a resultados de distritos subrepresentados (El Tambo, Chilca)
        for item in scored_results:
            if item["offer_row"].district in ["El Tambo", "Chilca"]:
                item["combined_score"] = min(item["combined_score"] * 1.05, 1.0)
        scored_results.sort(key=lambda x: x["combined_score"], reverse=True)
        reranking_applied = True
        logger.info(
            "equity_reranking_applied",
            worker_id=str(worker.id),
            disparate_impact=disparate_impact,
        )

    # Registrar en equity_audit_logs
    log_entry = EquityAuditLog(
        id=uuid.uuid4(),
        worker_id=worker.id,
        worker_type=worker.worker_type,
        district=worker.district,
        disparate_impact=disparate_impact,
        reranking_applied=reranking_applied,
    )
    db.add(log_entry)
    await db.commit()

    return scored_results
```

---

## PASO 7 — Explainer de recomendaciones (RF146–RF150)

Crea `app/ml/explainer/explainer.py`:

```python
# app/ml/explainer/explainer.py
"""
Explicador de recomendaciones — por qué se recomienda una oferta.
Cubre RF146–RF150 (M10 / Equidad y Explicabilidad).
Lenguaje en español coloquial, orientado al trabajador de Junín.
"""
from dataclasses import dataclass
from app.core.types import WorkerType
from app.models import Worker


@dataclass
class MatchExplanation:
    matching_skills: list[str]     # skills que coinciden
    missing_skills: list[str]      # skills de la oferta que el trabajador no tiene
    district_note: str             # nota sobre ubicación
    compatibility_label: str       # "Alta", "Media", "Baja"
    main_reason: str               # texto corto principal


def build_match_explanation(
    worker: Worker,
    offer_row,
    cosine_sim: float,
    skill_overlap: float,
    worker_type: WorkerType,
) -> MatchExplanation:
    """
    Construye explicación en lenguaje sencillo para el trabajador.
    Diferenciada por tipo para usar terminología apropiada.
    """
    worker_skills = set(worker.skills or [])
    offer_skills = set(offer_row.required_skills or [])
    
    matching = list(worker_skills & offer_skills)
    missing = list(offer_skills - worker_skills)[:3]  # máx 3 skills faltantes

    # Compatibilidad por score combinado
    if cosine_sim >= 0.80:
        compat = "Alta"
    elif cosine_sim >= 0.60:
        compat = "Media"
    else:
        compat = "Baja"

    # Nota de distrito
    if worker.district == offer_row.district:
        district_note = f"Este trabajo está en {offer_row.district}, tu mismo distrito."
    else:
        district_note = f"Este trabajo está en {offer_row.district}."

    # Razón principal diferenciada por tipo
    if worker_type == WorkerType.PRIMER_EMPLEO:
        if matching:
            main_reason = f"Tus habilidades de {', '.join(matching[:2])} encajan con lo que buscan."
        else:
            main_reason = "Esta oferta es buena para empezar tu trayectoria laboral."
    elif worker_type == WorkerType.OFICIO:
        if matching:
            main_reason = f"Tu experiencia en {', '.join(matching[:2])} es exactamente lo que necesitan."
        else:
            main_reason = f"Tu oficio como {worker.trade_category} es compatible con esta oportunidad."
    else:  # EXPERIENCIA
        if matching:
            main_reason = f"Tu perfil en {', '.join(matching[:2])} coincide con el puesto."
        else:
            main_reason = "Tu experiencia profesional es relevante para esta posición."

    return MatchExplanation(
        matching_skills=matching,
        missing_skills=missing,
        district_note=district_note,
        compatibility_label=compat,
        main_reason=main_reason,
    )
```

---

## PASO 8 — Entrenamiento del modelo supervisado

Crea `app/ml/matching_engine/trainer.py`:

```python
# app/ml/matching_engine/trainer.py
"""
Entrenamiento del clasificador supervisado de matching.
Algoritmo: GradientBoostingClassifier con random_state=42 (reproducibilidad).
Cubre RF086–RF095 (M05).
"""
import pickle
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import structlog

from app.ml.matching_engine.features import FEATURE_NAMES
from app.core.config import settings

logger = structlog.get_logger()

MODEL_DIR = Path("app/ml/models")
F1_MINIMUM = 0.75   # umbral del CLAUDE.md
F1_ALERT   = 0.70   # umbral de alerta


def train_matching_model(
    X: np.ndarray,
    y: np.ndarray,
    worker_type: str = "all",
    deploy_if_better: bool = True,
) -> dict:
    """
    Entrena el modelo de matching y lo guarda si supera F1 mínimo.
    random_state=42 para reproducibilidad (regla del CLAUDE.md).
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,         # ✅ SIEMPRE random_state=42
            subsample=0.8,
        ))
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    metrics = {
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
    }

    logger.info("model_trained", worker_type=worker_type, **metrics)

    if metrics["f1"] < F1_ALERT:
        logger.error(
            "model_f1_below_alert_threshold",
            f1=metrics["f1"],
            threshold=F1_ALERT,
            worker_type=worker_type,
            action="ALERT_REQUIRED — notificar al equipo",
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
        version_tag = f"v{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}-{worker_type}"
        model_path = MODEL_DIR / f"matching_{worker_type}_{version_tag}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(pipeline, f)
        
        # Marcar como activo en BD (via script externo o tarea Celery)
        logger.info("model_deployed", path=str(model_path), version=version_tag)
        return {"deployed": True, "metrics": metrics, "model_path": str(model_path), "version": version_tag}

    return {"deployed": False, "metrics": metrics}
```

---

## PASO 9 — Endpoint de matching

Crea `app/api/v1/matching.py`:

```python
# app/api/v1/matching.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import require_role, UserRole
from app.models import User, Worker
from app.ml.matching_engine.engine import match_worker_to_jobs
from app.schemas.matching import MatchResponse

router = APIRouter(prefix="/api/v1", tags=["matching"])


@router.get("/match/{worker_id}", response_model=MatchResponse)
async def get_matches(
    worker_id: UUID,
    top_k: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    """
    RF076–RF095: Obtener recomendaciones de empleo para un trabajador.
    Diferenciado por worker_type. Incluye explicaciones de compatibilidad.
    """
    # Verificar que el worker pertenece al usuario actual (o es admin)
    from sqlalchemy import select
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    if worker.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Sin autorización")

    matches = await match_worker_to_jobs(worker_id=worker_id, db=db, top_k=top_k)
    return MatchResponse(worker_id=worker_id, matches=matches, total=len(matches))
```

---

## PASO 10 — Tests obligatorios

```bash
# Crear tests
touch tests/unit/test_matching_engine.py
touch tests/unit/test_cold_start.py
touch tests/unit/test_equity_ranker.py
touch tests/unit/test_explainer.py
touch tests/integration/test_api_matching.py
```

**`tests/unit/test_matching_engine.py`** debe cubrir:
- `combined_score()` con los 3 tipos: verificar pesos exactos del CLAUDE.md
- Que PRIMER_EMPLEO siempre retorna `gamma=0` (sin reputación)
- `build_feature_vector()` retorna array de 9 elementos
- Que `random_state=42` está en el pipeline (reproducibilidad)

**`tests/unit/test_cold_start.py`** debe cubrir:
- Cold-start PRIMER_EMPLEO con wizard progress vacío
- Cold-start PRIMER_EMPLEO con skills extraídas
- Cold-start OFICIO con portfolio entries
- Cold-start OFICIO sin portfolio (solo metadata)
- Cold-start EXPERIENCIA desde campos de perfil

**`tests/integration/test_api_matching.py`** debe cubrir:
- `GET /api/v1/match/{worker_id}` retorna 200 con lista de matches
- Sin token → 401
- Worker de otro usuario → 403
- Worker sin embedding → activa cold-start y retorna resultados

```bash
# Ejecutar todos los tests
pytest tests/unit/test_matching_engine.py tests/unit/test_cold_start.py \
       tests/unit/test_equity_ranker.py tests/integration/test_api_matching.py \
       -v --cov=app/ml --cov-fail-under=80
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

```bash
# Verificar que el motor funciona
python -m app.ml.train --validate --worker-type all

# Migración aplicada
alembic current

# Tests pasan con cobertura ≥ 80%
pytest tests/unit/test_matching_engine.py tests/unit/test_cold_start.py -v

# Sin print()
grep -rn "print(" app/ml/

# Linting
ruff check app/ml/ app/api/v1/matching.py
```

**Archivos creados en esta instrucción:**
- `app/ml/matching_engine/features.py`
- `app/ml/matching_engine/scorer.py`
- `app/ml/matching_engine/engine.py`
- `app/ml/matching_engine/trainer.py`
- `app/ml/matching_engine/model_loader.py` (implementar carga de modelo .pkl activo)
- `app/ml/cold_start/resolver.py`
- `app/ml/equity_ranker/ranker.py`
- `app/ml/explainer/explainer.py`
- `app/api/v1/matching.py`
- `app/schemas/matching.py` (JobMatchResult, MatchResponse, MatchExplanation schemas)
- `alembic/versions/XXXX_add_ml_matching_tables.py`
- `tests/unit/test_matching_engine.py`
- `tests/unit/test_cold_start.py`
- `tests/unit/test_equity_ranker.py`
- `tests/integration/test_api_matching.py`

---

**Cuando termines, el agente `python-pro` con skill `python-fastapi` recibirá la instrucción 3
para implementar generación de CVs PDF (WeasyPrint), notificaciones WebSocket y alertas de empleo.**
