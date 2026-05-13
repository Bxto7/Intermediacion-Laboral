# RF: RF050-RF055 (M03) — Contratos laborales y calificaciones
from decimal import Decimal
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, require_role
from app.models.contract import Contract, Rating
from app.models.worker import Worker
from app.schemas.contract import ContractResponse, ContractStatusUpdate, RatingCreate, RatingResponse

router = APIRouter(prefix="/contracts", tags=["Contratos"])
logger = structlog.get_logger()


def _build_contract_response(c: Contract) -> ContractResponse:
    return ContractResponse(
        id=str(c.id),
        job_request_id=str(c.job_request_id),
        worker_id=str(c.worker_id),
        employer_id=str(c.employer_id),
        status=c.status,
        agreed_rate=c.agreed_rate,
        rate_type=c.rate_type,
        start_date=c.start_date,
        end_date=c.end_date,
        final_amount=c.final_amount,
        payment_method=c.payment_method,
        payment_confirmed=c.payment_confirmed,
        created_at=c.created_at,
    )


@router.get("/my", response_model=list[ContractResponse])
async def get_my_contracts(
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> list[ContractResponse]:
    """RF050 — Lista los contratos del trabajador autenticado."""
    worker_res = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
    worker = worker_res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    res = await db.execute(
        select(Contract)
        .where(Contract.worker_id == str(worker.id))
        .order_by(Contract.created_at.desc())
    )
    return [_build_contract_response(c) for c in res.scalars().all()]


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: str,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    """RF051 — Detalle de un contrato."""
    worker_res = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
    worker = worker_res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    res = await db.execute(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.worker_id == str(worker.id),
        )
    )
    contract = res.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return _build_contract_response(contract)


@router.patch("/{contract_id}/status", response_model=ContractResponse)
async def update_contract_status(
    contract_id: str,
    body: ContractStatusUpdate,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    """RF052 — Actualiza el estado del contrato (IN_PROGRESS, COMPLETED, CANCELLED)."""
    worker_res = await db.execute(select(Worker).where(Worker.user_id == payload["sub"]))
    worker = worker_res.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    res = await db.execute(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.worker_id == str(worker.id),
        )
    )
    contract = res.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    contract.status = body.status
    if body.cancelled_reason:
        contract.cancelled_reason = body.cancelled_reason
    if body.final_amount is not None:
        contract.final_amount = Decimal(str(body.final_amount))
    if body.payment_method:
        contract.payment_method = body.payment_method
    if body.status == "COMPLETED":
        contract.payment_confirmed = True

    await db.commit()
    await db.refresh(contract)

    if body.status == "COMPLETED":
        try:
            from app.integrations.drtpe.connector import drtpe_connector
            await drtpe_connector.report_placement(
                contract_id=contract_id,
                data={"worker_id": str(worker.id), "status": "COMPLETED"},
            )
        except Exception as exc:
            logger.warning("drtpe_placement_report_failed", error=str(exc))

    logger.info("contract_status_updated", contract_id=contract_id, new_status=body.status)
    return _build_contract_response(contract)


@router.post("/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(
    body: RatingCreate,
    payload: dict = Depends(require_role(UserRole.WORKER)),
    db: AsyncSession = Depends(get_db),
) -> RatingResponse:
    """RF053 — Califica al empleador o al trabajador tras completar contrato."""
    from app.models.user import User
    import uuid as uuid_mod

    user_res = await db.execute(select(User).where(User.id == payload["sub"]))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    contract_res = await db.execute(
        select(Contract).where(Contract.id == str(body.contract_id))
    )
    contract = contract_res.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    if contract.status != "COMPLETED":
        raise HTTPException(status_code=409, detail="Solo se puede calificar contratos completados")

    rater_role: Literal["worker", "employer"] = (
        "worker" if str(contract.worker_id) in [payload["sub"]]
        else "employer"
    )

    existing = await db.execute(
        select(Rating).where(
            Rating.contract_id == str(body.contract_id),
            Rating.rater_id == payload["sub"],
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe una calificación tuya para este contrato")

    from decimal import Decimal as D
    rating = Rating(
        id=str(uuid_mod.uuid4()),
        contract_id=str(body.contract_id),
        rater_id=payload["sub"],
        rated_id=str(body.rated_id),
        rater_role=rater_role,
        overall_score=D(str(body.overall_score)),
        quality_score=D(str(body.quality_score)) if body.quality_score else None,
        punctuality_score=D(str(body.punctuality_score)) if body.punctuality_score else None,
        communication_score=D(str(body.communication_score)) if body.communication_score else None,
        fairness_score=D(str(body.fairness_score)) if body.fairness_score else None,
        comment=body.comment,
    )
    db.add(rating)
    await db.commit()
    await db.refresh(rating)

    # Actualizar avg_rating del trabajador
    if rater_role == "employer":
        worker_res = await db.execute(
            select(Worker).where(Worker.id == str(contract.worker_id))
        )
        worker = worker_res.scalar_one_or_none()
        if worker:
            all_ratings_res = await db.execute(
                select(Rating).where(
                    Rating.rated_id == str(contract.worker_id),
                    Rating.rater_role == "employer",
                )
            )
            all_ratings = all_ratings_res.scalars().all()
            if all_ratings:
                avg = sum(float(r.overall_score) for r in all_ratings) / len(all_ratings)
                worker.avg_rating = D(str(round(avg, 2)))
                await db.commit()

    logger.info("rating_created", contract_id=str(body.contract_id), rater_role=rater_role)
    return RatingResponse(
        id=str(rating.id),
        contract_id=str(rating.contract_id),
        rater_id=str(rating.rater_id),
        rated_id=str(rating.rated_id),
        rater_role=rating.rater_role,
        overall_score=float(rating.overall_score),
        quality_score=float(rating.quality_score) if rating.quality_score else None,
        punctuality_score=float(rating.punctuality_score) if rating.punctuality_score else None,
        communication_score=float(rating.communication_score) if rating.communication_score else None,
        fairness_score=float(rating.fairness_score) if rating.fairness_score else None,
        comment=rating.comment,
        sentiment=rating.sentiment,
        created_at=rating.created_at,
    )
