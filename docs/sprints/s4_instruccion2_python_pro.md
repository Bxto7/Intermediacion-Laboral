# SPRINT 4 — INSTRUCCIÓN 2 de 5
# Agente: `python-pro`
# Skills a cargar: `skills/python-fastapi`, `skills/senior-backend`
# Tarea: Panel Admin DRTPE + KPIs de la tesis + encuestas económicas + conector DRTPE stub

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
La instrucción 1 del Sprint 4 ya aplicó:
- Rate limiting global (1000 req/min)
- AES-256 para `monthly_income`
- consent_records table
- Router admin con RBAC ADMIN obligatorio

**RF que implementas:** RF136–RF145 (M09 Reportes DRTPE), RF161–RF165 (M12 Integración Institucional)

---

## PARTE A — KPIs de la tesis (7 indicadores)

Los KPIs son el núcleo de los reportes para la DRTPE. El cálculo debe ser exacto
y corresponder a las fórmulas del CLAUDE.md.

Crea `app/services/reports/kpi_calculator.py`:

```python
# app/services/reports/kpi_calculator.py
"""
Cálculo de los 8 KPIs de la tesis (subcap. 4.3.2).
NUNCA modificar las fórmulas sin validación del equipo investigador.
Cubre RF136–RF145 (M09).
"""
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, text
import structlog

from app.models import Worker, Contract, SearchLog, GeneratedCV, ServiceListing, MatchEvent
from app.core.encryption import decrypt_field

logger = structlog.get_logger()


async def calculate_all_kpis(db: AsyncSession) -> dict:
    """
    Calcula y retorna los 8 KPIs de la tesis.
    Llamado por Celery Beat (diario 6am) y por el endpoint del panel admin.
    """
    kpis = {
        "vil":  await calculate_vil(db),
        "ivp":  await calculate_ivp(db),
        "tf":   await calculate_tasa_formalizacion(db),
        "rbs":  await calculate_rbs(db),
        "tcc":  await calculate_tcc(db),
        "ivm":  await calculate_ivm(db),
        "tcss": await calculate_tcss(db),
        "calculated_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.info("kpis_calculated", **{k: v for k, v in kpis.items() if k != "calculated_at"})
    return kpis


async def calculate_vil(db: AsyncSession) -> dict:
    """
    VIL — Velocidad de Inserción Laboral
    Fórmula: días(registro → primer contrato) — promedio por worker_type
    Tabla: contracts JOIN workers
    """
    result = await db.execute(text("""
        SELECT
            w.worker_type,
            AVG(
                EXTRACT(EPOCH FROM (c.signed_at - w.created_at)) / 86400.0
            )::DECIMAL(10,2) AS avg_days_to_first_contract,
            COUNT(*) AS sample_size
        FROM contracts c
        JOIN workers w ON c.worker_id = w.id
        WHERE c.contract_number = 1  -- primer contrato
          AND c.signed_at IS NOT NULL
        GROUP BY w.worker_type
    """))
    rows = result.fetchall()
    return {
        row.worker_type: {
            "avg_days": float(row.avg_days_to_first_contract or 0),
            "n": int(row.sample_size),
        }
        for row in rows
    }


async def calculate_ivp(db: AsyncSession) -> dict:
    """
    IVP — Índice de Visibilidad de Perfil
    Fórmula: (apariciones en búsquedas / total consultas) × 100
    Tabla: search_logs
    """
    result = await db.execute(text("""
        SELECT
            w.worker_type,
            COUNT(sl.id) AS total_appearances,
            (SELECT COUNT(*) FROM search_logs) AS total_queries,
            ROUND(
                100.0 * COUNT(sl.id) / NULLIF((SELECT COUNT(*) FROM search_logs), 0),
                2
            ) AS ivp_percent
        FROM search_logs sl
        JOIN workers w ON sl.worker_id = w.id
        GROUP BY w.worker_type
    """))
    rows = result.fetchall()
    return {
        row.worker_type: {
            "ivp_percent": float(row.ivp_percent or 0),
            "appearances": int(row.total_appearances),
        }
        for row in rows
    }


async def calculate_tasa_formalizacion(db: AsyncSession) -> dict:
    """
    TF — Tasa de Formalización
    Fórmula: (trabajadores con ≥1 contrato / total registrados) × 100
    Tablas: workers, contracts
    """
    result = await db.execute(text("""
        SELECT
            w.worker_type,
            COUNT(DISTINCT w.id) AS total_workers,
            COUNT(DISTINCT c.worker_id) AS workers_with_contract,
            ROUND(
                100.0 * COUNT(DISTINCT c.worker_id) / NULLIF(COUNT(DISTINCT w.id), 0),
                2
            ) AS tasa_percent
        FROM workers w
        LEFT JOIN contracts c ON c.worker_id = w.id
        GROUP BY w.worker_type
    """))
    rows = result.fetchall()
    return {
        row.worker_type: {
            "tasa_percent": float(row.tasa_percent or 0),
            "total": int(row.total_workers),
            "with_contract": int(row.workers_with_contract),
        }
        for row in rows
    }


async def calculate_rbs(db: AsyncSession) -> dict:
    """
    RBS — Reducción Brecha Salarial
    Fórmula: ((ingreso_post - ingreso_pre) / ingreso_pre) × 100
    Tabla: economic_surveys (cifrado AES — descifrar en memoria, no loggear)
    Solo aplica a workers que tienen survey PRE y POST.
    """
    result = await db.execute(text("""
        SELECT
            w.worker_type,
            pre.worker_id,
            pre.monthly_income AS income_pre_encrypted,
            post.monthly_income AS income_post_encrypted
        FROM economic_surveys pre
        JOIN economic_surveys post ON pre.worker_id = post.worker_id
            AND post.survey_phase = 'post'
        JOIN workers w ON pre.worker_id = w.id
        WHERE pre.survey_phase = 'pre'
          AND pre.consent_given = true
          AND post.consent_given = true
    """))
    rows = result.fetchall()

    by_type = {}
    for row in rows:
        try:
            income_pre  = float(decrypt_field(row.income_pre_encrypted))
            income_post = float(decrypt_field(row.income_post_encrypted))
            if income_pre > 0:
                change_pct = ((income_post - income_pre) / income_pre) * 100
                wtype = row.worker_type
                if wtype not in by_type:
                    by_type[wtype] = []
                by_type[wtype].append(change_pct)
        except Exception:
            pass  # no loggear datos económicos

    return {
        wtype: {
            "avg_change_percent": round(sum(vals) / len(vals), 2),
            "n": len(vals),
        }
        for wtype, vals in by_type.items()
    }


async def calculate_tcc(db: AsyncSession) -> dict:
    """
    TCC — Tasa de Completitud de CV
    Fórmula: (perfiles con CV generado / total registrados) × 100
    Aplica: PRIMER_EMPLEO y OFICIO
    Tablas: generated_cvs, workers
    """
    result = await db.execute(text("""
        SELECT
            w.worker_type,
            COUNT(DISTINCT w.id) AS total,
            COUNT(DISTINCT gc.worker_id) AS with_cv,
            ROUND(
                100.0 * COUNT(DISTINCT gc.worker_id) / NULLIF(COUNT(DISTINCT w.id), 0),
                2
            ) AS tcc_percent
        FROM workers w
        LEFT JOIN generated_cvs gc ON gc.worker_id = w.id
        WHERE w.worker_type IN ('primer_empleo', 'oficio')
        GROUP BY w.worker_type
    """))
    rows = result.fetchall()
    return {
        row.worker_type: {
            "tcc_percent": float(row.tcc_percent or 0),
            "total": int(row.total),
            "with_cv": int(row.with_cv),
        }
        for row in rows
    }


async def calculate_ivm(db: AsyncSession) -> dict:
    """
    IVM — Índice de Visibilidad en Marketplace
    Fórmula: (listados activos / total trabajadores OFICIO) × 100
    Solo aplica a OFICIO.
    Tablas: service_listings, workers
    """
    result = await db.execute(text("""
        SELECT
            COUNT(DISTINCT sl.id)::DECIMAL AS active_listings,
            COUNT(DISTINCT w.id)::DECIMAL AS total_oficio_workers,
            ROUND(
                100.0 * COUNT(DISTINCT sl.id) / NULLIF(COUNT(DISTINCT w.id), 0),
                2
            ) AS ivm_percent
        FROM workers w
        LEFT JOIN service_listings sl ON sl.worker_id = w.id AND sl.is_active = true
        WHERE w.worker_type = 'oficio'
    """))
    row = result.fetchone()
    return {
        "ivm_percent": float(row.ivm_percent or 0),
        "active_listings": int(row.active_listings or 0),
        "total_oficio": int(row.total_oficio_workers or 0),
    }


async def calculate_tcss(db: AsyncSession) -> dict:
    """
    TCSS — Tasa de Cold-Start Superado
    Fórmula: (usuarios primer_empleo/oficio con ≥1 match / total) × 100
    Tabla: match_events
    """
    result = await db.execute(text("""
        SELECT
            w.worker_type,
            COUNT(DISTINCT w.id) AS total,
            COUNT(DISTINCT me.worker_id) AS with_match,
            ROUND(
                100.0 * COUNT(DISTINCT me.worker_id) / NULLIF(COUNT(DISTINCT w.id), 0),
                2
            ) AS tcss_percent
        FROM workers w
        LEFT JOIN match_events me ON me.worker_id = w.id
        WHERE w.worker_type IN ('primer_empleo', 'oficio')
        GROUP BY w.worker_type
    """))
    rows = result.fetchall()
    return {
        row.worker_type: {
            "tcss_percent": float(row.tcss_percent or 0),
            "total": int(row.total),
            "with_match": int(row.with_match),
        }
        for row in rows
    }
```

---

## PARTE B — Panel Admin DRTPE (M09 / RF136–RF145)

Crea `app/api/v1/admin/dashboard.py`:

```python
# app/api/v1/admin/dashboard.py
"""
Panel de administración DRTPE-Junín.
Todos los endpoints requieren rol ADMIN (configurado en el router base).
Cubre RF136–RF145 (M09).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.db import get_db, get_redis
from app.services.reports.kpi_calculator import calculate_all_kpis
from app.schemas.admin import DashboardResponse, WorkerStatsResponse

router = APIRouter()  # prefix y auth heredados del admin_router


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    RF136–RF140: Dashboard principal con los 7 KPIs de la tesis.
    Cachear en Redis 1 hora (KPIs no cambian minuto a minuto).
    """
    cache_key = "admin:dashboard:kpis"
    cached = await redis.get(cache_key)
    if cached:
        import json
        return DashboardResponse(**json.loads(cached))

    kpis = await calculate_all_kpis(db)
    dashboard = DashboardResponse(**kpis)

    await redis.set(cache_key, dashboard.model_dump_json(), ex=3600)
    return dashboard


@router.get("/workers/stats", response_model=WorkerStatsResponse)
async def get_worker_stats(
    db: AsyncSession = Depends(get_db),
):
    """RF141–RF145: Estadísticas de workers por tipo y región."""
    from sqlalchemy import text
    result = await db.execute(text("""
        SELECT
            worker_type,
            district,
            COUNT(*) AS total,
            AVG(profile_completeness) AS avg_completeness,
            COUNT(*) FILTER (WHERE is_available = true) AS available
        FROM workers
        GROUP BY worker_type, district
        ORDER BY worker_type, district
    """))
    rows = result.fetchall()
    return WorkerStatsResponse(
        stats=[
            {
                "worker_type": r.worker_type,
                "district": r.district,
                "total": r.total,
                "avg_completeness": float(r.avg_completeness or 0),
                "available": r.available,
            }
            for r in rows
        ]
    )


@router.get("/model/metrics")
async def get_model_metrics(
    db: AsyncSession = Depends(get_db),
):
    """
    RF146–RF150: Métricas del modelo ML (F1, precision, recall, disparate impact).
    PROTEGIDO: solo ADMIN — el CLAUDE.md prohíbe exponer sin autenticación ADMIN.
    """
    from sqlalchemy import select
    from app.models import ModelVersion
    result = await db.execute(
        select(ModelVersion)
        .where(ModelVersion.is_active == True)
        .order_by(ModelVersion.deployed_at.desc())
    )
    versions = result.scalars().all()
    return {
        "active_models": [
            {
                "version": v.version_tag,
                "worker_type": v.worker_type,
                "f1_score": float(v.f1_score or 0),
                "precision": float(v.precision_score or 0),
                "recall": float(v.recall_score or 0),
                "deployed_at": v.deployed_at.isoformat() if v.deployed_at else None,
            }
            for v in versions
        ]
    }
```

---

## PARTE C — Encuestas económicas (Ley 29733)

Crea `app/api/v1/surveys.py`:

```python
# app/api/v1/surveys.py
"""
Encuestas económicas para el KPI Reducción Brecha Salarial.
Datos cifrados con AES-256. Consentimiento obligatorio (Ley 29733).
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import require_role, UserRole
from app.core.encryption import encrypt_field
from app.core.consent import require_consent
from app.models import EconomicSurvey, ConsentRecord, User, Worker
from app.schemas.surveys import EconomicSurveyCreate, EconomicSurveyResponse

router = APIRouter(prefix="/api/v1/surveys", tags=["surveys"])


@router.post("/economic", response_model=EconomicSurveyResponse)
async def create_economic_survey(
    data: EconomicSurveyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.WORKER)),
    request: Request = None,
):
    """
    Registrar encuesta económica (pre o post intervención).
    monthly_income se cifra con AES-256 antes de persistir.
    Requiere consentimiento explícito (Ley 29733).
    """
    import uuid as uuid_mod

    # Consentimiento Ley 29733 — obligatorio
    require_consent(data.consent_given, "datos_economicos")

    # Verificar que el worker pertenece al usuario
    from sqlalchemy import select
    res = await db.execute(select(Worker).where(Worker.id == data.worker_id))
    worker = res.scalar_one_or_none()
    if not worker or worker.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin autorización")

    # Cifrar ingreso mensual — NUNCA en texto plano en BD
    encrypted_income = encrypt_field(str(data.monthly_income))

    survey = EconomicSurvey(
        id=uuid_mod.uuid4(),
        worker_id=data.worker_id,
        survey_phase=data.survey_phase,
        monthly_income=encrypted_income,
        employment_type=data.employment_type,
        consent_given=True,
    )
    db.add(survey)

    # Registrar consentimiento en tabla de auditoría
    consent_record = ConsentRecord(
        id=uuid_mod.uuid4(),
        user_id=current_user.id,
        data_purpose="datos_economicos",
        ip_address=request.client.host if request else None,
        consent_given=True,
    )
    db.add(consent_record)

    await db.commit()
    return EconomicSurveyResponse(id=survey.id, survey_phase=survey.survey_phase)
```

---

## PARTE D — Conector DRTPE stub (M12 / RF161–RF165)

Crea `app/integrations/drtpe/connector.py`:

```python
# app/integrations/drtpe/connector.py
"""
Conector con la Bolsa de Trabajo oficial de la DRTPE-Junín.
Sprint 4: implementación stub con interfaz real.
Sprint 5: reemplazar stubs con llamadas reales a la API DRTPE.
Cubre RF161–RF165 (M12).
"""
from dataclasses import dataclass
from typing import Protocol
import structlog

logger = structlog.get_logger()


@dataclass
class DRTPEJobOffer:
    """Oferta de empleo proveniente de la Bolsa de Trabajo DRTPE."""
    external_id: str
    title: str
    employer_name: str
    district: str
    required_skills: list[str]
    salary_min: float | None
    salary_max: float | None
    published_at: str
    source: str = "DRTPE-JUNIN"


class DRTPEConnectorProtocol(Protocol):
    """Interfaz del conector DRTPE — permite swap de stub por implementación real."""
    async def fetch_active_offers(self, limit: int = 50) -> list[DRTPEJobOffer]: ...
    async def sync_worker_registration(self, worker_id: str, data: dict) -> bool: ...
    async def report_placement(self, contract_id: str, data: dict) -> bool: ...


class DRTPEConnectorStub:
    """
    Stub del conector DRTPE para desarrollo y testing.
    Retorna datos realistas de Junín para pruebas.
    Reemplazar en Sprint 5 por DRTPEConnectorReal.
    """

    async def fetch_active_offers(self, limit: int = 50) -> list[DRTPEJobOffer]:
        """
        Sprint 4: Retorna ofertas simuladas de la DRTPE-Junín.
        Sprint 5: GET https://api.drtpe.gob.pe/bolsa/ofertas
        """
        logger.info("drtpe_fetch_offers_stub", limit=limit)
        return [
            DRTPEJobOffer(
                external_id="DRTPE-2026-001",
                title="Técnico en instalaciones eléctricas",
                employer_name="Empresa Constructora El Tambo S.A.C.",
                district="El Tambo",
                required_skills=["instalación eléctrica", "lectura de planos"],
                salary_min=1500.0,
                salary_max=2200.0,
                published_at="2026-05-01",
            ),
            DRTPEJobOffer(
                external_id="DRTPE-2026-002",
                title="Auxiliar administrativo",
                employer_name="Municipalidad Provincial de Huancayo",
                district="Huancayo",
                required_skills=["office", "atención al cliente", "archivo"],
                salary_min=1025.0,
                salary_max=1400.0,
                published_at="2026-05-03",
            ),
            DRTPEJobOffer(
                external_id="DRTPE-2026-003",
                title="Gasfitero para mantenimiento",
                employer_name="Urbanización Los Jardines S.A.",
                district="Chilca",
                required_skills=["gasfitería", "plomería", "fontanería"],
                salary_min=1200.0,
                salary_max=1800.0,
                published_at="2026-05-04",
            ),
        ][:limit]

    async def sync_worker_registration(self, worker_id: str, data: dict) -> bool:
        """Sprint 4 stub: simula registro exitoso en DRTPE."""
        logger.info("drtpe_sync_registration_stub", worker_id=worker_id)
        return True

    async def report_placement(self, contract_id: str, data: dict) -> bool:
        """Sprint 4 stub: simula reporte de colocación laboral."""
        logger.info("drtpe_report_placement_stub", contract_id=contract_id)
        return True


# Instancia singleton del conector (cambiar en Sprint 5)
drtpe_connector: DRTPEConnectorProtocol = DRTPEConnectorStub()
```

### Tarea Celery para sincronización DRTPE

```python
# En app/tasks/reports.py — agregar:
@shared_task(name="tasks.sync_drtpe_offers")
def sync_drtpe_offers_task():
    """
    Sincronizar ofertas de la DRTPE con la BD local.
    Celery Beat: diario a las 8am Lima.
    """
    import asyncio
    from app.integrations.drtpe.connector import drtpe_connector

    async def _sync():
        offers = await drtpe_connector.fetch_active_offers(limit=100)
        # Upsert en job_offers con source='DRTPE-JUNIN'
        logger.info("drtpe_offers_synced", count=len(offers))

    asyncio.run(_sync())
```

---

## PARTE E — Schemas Pydantic v2 para el admin

Crea `app/schemas/admin.py`:

```python
# app/schemas/admin.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class KPIByType(BaseModel):
    avg_days: float = 0.0
    n: int = 0


class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # VIL — Velocidad Inserción Laboral (días promedio por tipo)
    vil: dict[str, KPIByType]
    # IVP — Índice Visibilidad Perfil (%)
    ivp: dict[str, dict]
    # TF — Tasa Formalización (%)
    tf: dict[str, dict]
    # RBS — Reducción Brecha Salarial (%)
    rbs: dict[str, dict]
    # TCC — Tasa Completitud CV (%)
    tcc: dict[str, dict]
    # IVM — Índice Visibilidad Marketplace (%) — solo OFICIO
    ivm: dict
    # TCSS — Tasa Cold-Start Superado (%)
    tcss: dict[str, dict]
    # Timestamp del cálculo
    calculated_at: str


class WorkerStatsResponse(BaseModel):
    stats: list[dict]
```

---

## PARTE F — Migraciones Sprint 4

```bash
alembic revision --autogenerate -m "add contracts search_logs tables sprint4"
alembic upgrade head
```

Tablas necesarias para los KPIs (si no existen):

```sql
-- Contratos (para VIL y TF)
CREATE TABLE contracts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id       UUID NOT NULL REFERENCES workers(id),
    employer_id     UUID REFERENCES employers(id),
    contract_number INTEGER DEFAULT 1,  -- 1=primer contrato, 2=segundo, etc.
    signed_at       TIMESTAMPTZ,
    contract_type   VARCHAR(30),        -- 'formal', 'informal', 'marketplace'
    monthly_salary  BYTEA,              -- AES-256
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON contracts (worker_id, contract_number);

-- Search logs (para IVP)
CREATE TABLE search_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id   UUID REFERENCES workers(id),  -- NULL si búsqueda sin resultado
    query_text  TEXT,
    results_count INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON search_logs (worker_id, created_at DESC);
```

---

## TESTS OBLIGATORIOS

```bash
touch tests/unit/test_kpi_calculator.py
touch tests/integration/test_api_admin_dashboard.py
touch tests/unit/test_drtpe_connector.py
```

**`tests/unit/test_kpi_calculator.py`** debe cubrir:
- `calculate_vil()` retorna dict con claves por worker_type
- `calculate_tcc()` solo incluye primer_empleo y oficio
- `calculate_ivm()` solo aplica a oficio
- `calculate_rbs()` descifra correctamente (mock de `decrypt_field`)
- Ningún KPI lanza excepción con BD vacía (retorna 0)

**`tests/integration/test_api_admin_dashboard.py`** debe cubrir:
- `GET /api/v1/admin/dashboard` sin token → 401
- Con token WORKER → 403
- Con token ADMIN → 200 con los 7 KPIs
- `GET /api/v1/admin/model/metrics` sin token ADMIN → 403

```bash
pytest tests/unit/test_kpi_calculator.py tests/integration/test_api_admin_dashboard.py -v
ruff check app/services/reports/ app/api/v1/admin/ app/integrations/drtpe/
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

- `app/services/reports/kpi_calculator.py` — 7 KPIs exactos del CLAUDE.md
- `app/api/v1/admin/dashboard.py` — panel admin con cache Redis
- `app/api/v1/surveys.py` — encuestas económicas cifradas
- `app/integrations/drtpe/connector.py` — conector stub M12
- `app/schemas/admin.py` — schemas Pydantic v2
- `alembic/versions/XXXX_contracts_search_logs.py`
- `tests/unit/test_kpi_calculator.py`
- `tests/integration/test_api_admin_dashboard.py`

---

**Cuando termines, el agente `ml-engineer` recibirá la instrucción 3 para el DatasetBuilder
real, drift detection PSI y métricas del modelo en producción.**
