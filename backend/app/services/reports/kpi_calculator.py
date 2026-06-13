# RF: RF136-RF145 (M09) — Cálculo de KPIs institucionales para panel DRTPE-Junín
from datetime import UTC, datetime

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_field

logger = structlog.get_logger()


async def calculate_vil(db: AsyncSession) -> dict:
    """Velocidad Inserción Laboral: días entre registro y primer contrato."""
    sql = text("""
        SELECT
            w.worker_type,
            ROUND(AVG(
                EXTRACT(EPOCH FROM (c.start_date::timestamptz - u.created_at)) / 86400
            )::numeric, 1) AS avg_days,
            COUNT(DISTINCT w.id) AS n
        FROM contracts c
        JOIN workers w ON w.id = c.worker_id
        JOIN users u ON u.id = w.user_id
        WHERE c.start_date IS NOT NULL
          AND c.status = 'CONFIRMED'
        GROUP BY w.worker_type
    """)
    rows = (await db.execute(sql)).fetchall()
    return {r.worker_type: {"avg_days": float(r.avg_days or 0), "n": r.n} for r in rows}


async def calculate_ivp(db: AsyncSession) -> dict:
    """Índice Visibilidad Perfil: (apariciones en búsqueda / total consultas) × 100."""
    sql = text("""
        SELECT
            w.worker_type,
            COUNT(me.id)::float / NULLIF(
                (SELECT COUNT(*) FROM search_logs), 0
            ) * 100 AS ivp_pct
        FROM match_events me
        JOIN workers w ON w.id = me.worker_id
        GROUP BY w.worker_type
    """)
    rows = (await db.execute(sql)).fetchall()
    return {r.worker_type: round(float(r.ivp_pct or 0), 2) for r in rows}


async def calculate_tf(db: AsyncSession) -> dict:
    """Tasa Formalización: (trabajadores con ≥1 contrato / total registrados) × 100."""
    sql = text("""
        SELECT
            w.worker_type,
            COUNT(DISTINCT c.worker_id)::float /
                NULLIF(COUNT(DISTINCT w.id), 0) * 100 AS tf_pct
        FROM workers w
        LEFT JOIN contracts c ON c.worker_id = w.id
        GROUP BY w.worker_type
    """)
    rows = (await db.execute(sql)).fetchall()
    return {r.worker_type: round(float(r.tf_pct or 0), 2) for r in rows}


async def calculate_rbs(db: AsyncSession) -> dict:
    """Reducción Brecha Salarial: ((ingreso_post - ingreso_pre) / ingreso_pre) × 100.
    monthly_income está cifrado con AES-256; se descifra en Python."""
    sql = text("""
        SELECT worker_id, survey_phase, monthly_income
        FROM economic_surveys
        WHERE consent_given = true AND survey_phase IN ('pre', 'post')
        ORDER BY worker_id, survey_phase
    """)
    rows = (await db.execute(sql)).fetchall()

    pairs: dict[str, dict] = {}
    for r in rows:
        wid = str(r.worker_id)
        if wid not in pairs:
            pairs[wid] = {}
        try:
            income = float(decrypt_field(r.monthly_income))
        except Exception:
            continue
        pairs[wid][r.survey_phase] = income

    deltas = [
        (v["post"] - v["pre"]) / v["pre"] * 100
        for v in pairs.values()
        if "pre" in v and "post" in v and v["pre"] > 0
    ]
    avg_rbs = round(sum(deltas) / len(deltas), 2) if deltas else 0.0
    return {"avg_pct": avg_rbs, "n_pairs": len(deltas)}


async def calculate_tcc(db: AsyncSession) -> dict:
    """Tasa Completitud CV: (perfiles con CV generado / total) × 100.
    Solo aplica a PRIMER_EMPLEO y OFICIO."""
    sql = text("""
        SELECT
            w.worker_type,
            COUNT(DISTINCT g.worker_id)::float /
                NULLIF(COUNT(DISTINCT w.id), 0) * 100 AS tcc_pct
        FROM workers w
        LEFT JOIN generated_cvs g ON g.worker_id = w.id
        WHERE w.worker_type IN ('primer_empleo', 'oficio')
        GROUP BY w.worker_type
    """)
    rows = (await db.execute(sql)).fetchall()
    return {r.worker_type: round(float(r.tcc_pct or 0), 2) for r in rows}


async def calculate_ivm(db: AsyncSession) -> dict:
    """Índice Visibilidad Marketplace: (listados activos / total OFICIO) × 100."""
    sql = text("""
        SELECT
            COUNT(CASE WHEN sl.is_active THEN 1 END)::float /
                NULLIF(COUNT(DISTINCT w.id), 0) * 100 AS ivm_pct,
            COUNT(DISTINCT w.id) AS total_oficio
        FROM workers w
        LEFT JOIN service_listings sl ON sl.worker_id = w.id
        WHERE w.worker_type = 'oficio'
    """)
    row = (await db.execute(sql)).fetchone()
    if row is None:
        return {"ivm_pct": 0.0, "total_oficio": 0}
    return {
        "ivm_pct": round(float(row.ivm_pct or 0), 2),
        "total_oficio": row.total_oficio or 0,
    }


async def calculate_tcss(db: AsyncSession) -> dict:
    """Tasa Cold-Start Superado: (usuarios PE/OFICIO con ≥1 match / total) × 100."""
    sql = text("""
        SELECT
            w.worker_type,
            COUNT(DISTINCT me.worker_id)::float /
                NULLIF(COUNT(DISTINCT w.id), 0) * 100 AS tcss_pct
        FROM workers w
        LEFT JOIN match_events me ON me.worker_id = w.id
        WHERE w.worker_type IN ('primer_empleo', 'oficio')
        GROUP BY w.worker_type
    """)
    rows = (await db.execute(sql)).fetchall()
    return {r.worker_type: round(float(r.tcss_pct or 0), 2) for r in rows}


async def calculate_all_kpis(db: AsyncSession) -> dict:
    """Ejecuta los 7 KPIs y retorna el DashboardResponse dict.

    IMPORTANTE: las queries se ejecutan SECUENCIALMENTE, no con asyncio.gather.
    asyncpg no permite operaciones concurrentes sobre la misma conexión/sesión;
    hacerlo en paralelo lanzaba "another operation is in progress" en cada query
    y dejaba todos los KPIs en cero.
    """
    async def safe(coro, fallback):
        try:
            return await coro
        except Exception as exc:  # noqa: BLE001
            logger.warning("kpi_calculation_failed", error=str(exc))
            return fallback

    return {
        "vil": await safe(calculate_vil(db), {}),
        "ivp": await safe(calculate_ivp(db), {}),
        "tf": await safe(calculate_tf(db), {}),
        "rbs": await safe(calculate_rbs(db), {"avg_pct": 0.0, "n_pairs": 0}),
        "tcc": await safe(calculate_tcc(db), {}),
        "ivm": await safe(calculate_ivm(db), {"ivm_pct": 0.0, "total_oficio": 0}),
        "tcss": await safe(calculate_tcss(db), {}),
        "calculated_at": datetime.now(UTC).isoformat(),
    }
