# RF: RF136-RF145 (M09) + RF156-RF160 (M11) — Panel admin DRTPE: dashboard y métricas
import json
from datetime import UTC, datetime

import structlog
from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.admin import admin_router
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.security import decrypt_field
from app.ml.matching_engine.model_loader import load_model_metrics
from app.schemas.admin import DashboardResponse, WorkerStatsResponse
from app.services.reports.kpi_calculator import calculate_all_kpis

logger = structlog.get_logger()

DASHBOARD_CACHE_KEY = "admin:dashboard:v1"
DASHBOARD_CACHE_TTL = 3600  # 1 hora


@admin_router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
):
    """Dashboard consolidado de KPIs institucionales. Cache Redis 1 h."""
    redis = get_redis()

    try:
        cached = await redis.get(DASHBOARD_CACHE_KEY)
        if cached:
            return DashboardResponse(**json.loads(cached))
    except Exception:
        pass

    kpis = await calculate_all_kpis(db)

    try:
        await redis.setex(DASHBOARD_CACHE_KEY, DASHBOARD_CACHE_TTL, json.dumps(kpis))
    except Exception:
        pass

    logger.info("dashboard_computed", calculated_at=kpis["calculated_at"])
    return DashboardResponse(**kpis)


@admin_router.get("/workers/stats", response_model=WorkerStatsResponse)
async def get_worker_stats(db: AsyncSession = Depends(get_db)):
    """Estadísticas agregadas de trabajadores por tipo, distrito y completitud."""
    sql = text("""
        SELECT
            worker_type,
            district,
            COUNT(*) AS total,
            ROUND(AVG(profile_completeness), 1) AS avg_completeness,
            COUNT(CASE WHEN is_available THEN 1 END) AS available
        FROM workers
        GROUP BY worker_type, district
        ORDER BY worker_type, total DESC
    """)
    rows = (await db.execute(sql)).fetchall()
    stats = [
        {
            "worker_type": r.worker_type,
            "district": r.district,
            "total": r.total,
            "avg_completeness": float(r.avg_completeness or 0),
            "available": r.available,
        }
        for r in rows
    ]
    return WorkerStatsResponse(stats=stats)


@admin_router.get("/model/metrics")
async def get_model_metrics():
    """Métricas del modelo ML activo (F1, precision, recall por worker_type).
    Requiere autenticación ADMIN — definida en admin_router dependencies."""
    try:
        metrics = load_model_metrics()
        return {"metrics": metrics, "queried_at": datetime.now(UTC).isoformat()}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No hay modelo entrenado disponible.")


@admin_router.get("/model/drift")
async def get_drift_status():
    """Estado PSI de drift del modelo por worker_type."""
    try:
        from app.ml.matching_engine.drift_detector import check_all_types_drift
        result = check_all_types_drift()
        return {"drift": result, "checked_at": datetime.now(UTC).isoformat()}
    except Exception as exc:
        logger.warning("drift_check_failed", error=str(exc))
        raise HTTPException(status_code=503, detail="Datos de drift no disponibles.")


@admin_router.post("/dashboard/invalidate-cache")
async def invalidate_dashboard_cache():
    """Invalida el cache del dashboard para forzar recálculo inmediato."""
    redis = get_redis()
    try:
        await redis.delete(DASHBOARD_CACHE_KEY)
    except Exception:
        pass
    return {"invalidated": True}


@admin_router.get("/workers")
async def list_workers(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Lista de trabajadores con datos básicos para el panel admin."""
    sql = text("""
        SELECT
            w.id,
            u.email,
            w.full_name,
            w.worker_type,
            w.district,
            w.trade_category,
            w.profile_completeness,
            w.is_available,
            u.created_at
        FROM workers w
        JOIN users u ON u.id = w.user_id
        ORDER BY u.created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    rows = (await db.execute(sql, {"limit": limit, "offset": offset})).fetchall()

    total_sql = text("SELECT COUNT(*) FROM workers")
    total = (await db.execute(total_sql)).scalar() or 0

    workers = []
    for r in rows:
        try:
            name = decrypt_field(r.full_name) if r.full_name else r.email
        except Exception:
            name = r.email
        workers.append({
            "id": str(r.id),
            "email": r.email,
            "name": name,
            "worker_type": r.worker_type,
            "district": r.district or "—",
            "trade_category": r.trade_category or "—",
            "profile_completeness": r.profile_completeness,
            "is_available": r.is_available,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {"workers": workers, "total": total}


@admin_router.get("/employers")
async def list_employers(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Lista de empleadores con conteo real de ofertas y postulantes para el panel admin."""
    sql = text("""
        SELECT
            e.id,
            u.email,
            e.company_name,
            e.district,
            e.sector,
            e.is_verified,
            u.created_at,
            (SELECT COUNT(*) FROM job_offers jo WHERE jo.employer_id = e.id) AS jobs,
            (SELECT COUNT(*) FROM applications a
                JOIN job_offers jo2 ON jo2.id = a.job_offer_id
                WHERE jo2.employer_id = e.id) AS candidates
        FROM employers e
        JOIN users u ON u.id = e.user_id
        ORDER BY u.created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    rows = (await db.execute(sql, {"limit": limit, "offset": offset})).fetchall()
    total = (await db.execute(text("SELECT COUNT(*) FROM employers"))).scalar() or 0

    employers = [
        {
            "id": str(r.id),
            "email": r.email,
            "company_name": r.company_name or r.email,
            "district": r.district or "—",
            "sector": r.sector or "—",
            "is_verified": r.is_verified,
            "jobs": int(r.jobs or 0),
            "candidates": int(r.candidates or 0),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

    return {"employers": employers, "total": total}
