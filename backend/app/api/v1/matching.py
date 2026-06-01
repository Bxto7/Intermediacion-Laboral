# RF: RF076-RF095 (M05) — motor de matching diferenciado por worker_type
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, require_role
from app.ml.equity_ranker.ranker import (
    apply_equity_reranking,
    compute_disparate_impact,
    log_equity_audit,
)
from app.ml.explainer.explainer import explain_match
from app.ml.matching_engine.scorer import combined_score
from app.models.job_offer import JobOffer
from app.models.worker import Worker

logger = structlog.get_logger()
router = APIRouter(prefix="/match", tags=["matching"])


class MatchExplanationOut(BaseModel):
    matching_skills: list[str]
    missing_skills: list[str]
    compatibility_label: str
    message: str


class JobMatchOut(BaseModel):
    job_id: str
    title: str
    district: str | None
    combined_score: float
    rank: int
    explanation: MatchExplanationOut


class MatchResponseOut(BaseModel):
    worker_id: str
    worker_type: str
    matches: list[JobMatchOut]
    total: int


@router.get("/{worker_id}", response_model=MatchResponseOut)
async def match_worker(
    worker_id: UUID,
    top_k: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WORKER)),
):
    """
    RF076-RF095: Motor de matching diferenciado por worker_type.
    Retorna top-K ofertas ordenadas por combined_score con explicacion.
    """
    token_user_id = current_user.get("sub", "")

    res = await db.execute(select(Worker).where(Worker.id == str(worker_id)))
    worker = res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    if str(worker.user_id) != token_user_id:
        raise HTTPException(status_code=403, detail="No puedes ver recomendaciones de otro trabajador")

    # Obtener ofertas activas
    offers_res = await db.execute(
        select(JobOffer).where(JobOffer.is_active.is_(True)).limit(top_k * 5)
    )
    offers = offers_res.scalars().all()

    if not offers:
        return MatchResponseOut(
            worker_id=str(worker_id),
            worker_type=worker.worker_type,
            matches=[],
            total=0,
        )

    worker_skills: list[str] = []
    if worker.worker_type == "primer_empleo":
        from app.models.wizard import WizardProgress
        w_res = await db.execute(select(WizardProgress).where(WizardProgress.worker_id == str(worker.id)))
        wiz = w_res.scalar_one_or_none()
        if wiz:
            worker_skills = list(wiz.extracted_skills or [])
    elif worker.worker_type == "oficio":
        from app.models.portfolio import PortfolioEntry
        p_res = await db.execute(select(PortfolioEntry).where(PortfolioEntry.worker_id == str(worker.id)))
        entries = p_res.scalars().all()
        for entry in entries:
            worker_skills.extend(entry.extracted_skills or [])

    reputation = float(worker.avg_rating or 0)
    matches_raw: list[dict] = []

    for offer in offers:
        cosine_sim = 0.5
        ml_score = 0.5

        # Cosine similarity via embedding if available
        if worker.embedding is not None and offer.embedding is not None:
            try:
                import numpy as np
                w_vec = np.array(worker.embedding)
                o_vec = np.array(offer.embedding)
                cosine_sim = float(np.dot(w_vec, o_vec) / (np.linalg.norm(w_vec) * np.linalg.norm(o_vec) + 1e-8))
                cosine_sim = max(0.0, min(1.0, cosine_sim))
            except Exception:  # noqa: S110
                pass

        score = combined_score(cosine_sim, ml_score, reputation, worker.worker_type)
        explanation = explain_match(
            combined_score=score,
            worker_skills=worker_skills,
            offer_required_skills=list(offer.required_skills or []),
            offer_preferred_skills=list(offer.preferred_skills or []),
            worker_type=worker.worker_type,
        )

        matches_raw.append({
            "job_id": str(offer.id),
            "title": offer.title,
            "district": offer.district,
            "combined_score": score,
            "explanation": explanation,
        })

    # Equity re-ranking
    matches_raw = apply_equity_reranking(matches_raw, group_field="district")
    matches_raw = sorted(matches_raw, key=lambda m: m["combined_score"], reverse=True)[:top_k]

    # Disparate impact audit
    districts_map: dict[str, list[float]] = {}
    for m in matches_raw:
        d = m.get("district") or "unknown"
        districts_map.setdefault(d, []).append(m["combined_score"])

    groups = list(districts_map.values())
    if len(groups) >= 2:
        di = compute_disparate_impact(groups[0], groups[1])
        log_equity_audit(str(worker_id), worker.worker_type, di, di < 0.80)

    import uuid as uuid_mod

    from app.models.match_event import MatchEvent
    for rank, m in enumerate(matches_raw, 1):
        event = MatchEvent(
            id=uuid_mod.uuid4(),
            worker_id=str(worker_id),
            matched_job_id=m["job_id"],
            combined_score=m["combined_score"],
            rank_position=rank,
            worker_type=worker.worker_type,
        )
        db.add(event)
    try:
        await db.commit()
    except Exception:
        await db.rollback()

    result_matches = [
        JobMatchOut(
            job_id=m["job_id"],
            title=m["title"],
            district=m.get("district"),
            combined_score=m["combined_score"],
            rank=i + 1,
            explanation=MatchExplanationOut(
                matching_skills=m["explanation"]["matching_skills"],
                missing_skills=m["explanation"]["missing_skills"],
                compatibility_label=m["explanation"]["compatibility_label"],
                message=m["explanation"]["message"],
            ),
        )
        for i, m in enumerate(matches_raw)
    ]

    logger.info("matching_completed", worker_id=str(worker_id), worker_type=worker.worker_type, total=len(result_matches))

    return MatchResponseOut(
        worker_id=str(worker_id),
        worker_type=worker.worker_type,
        matches=result_matches,
        total=len(result_matches),
    )
