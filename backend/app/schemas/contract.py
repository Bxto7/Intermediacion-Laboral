# RF: RF036-RF055 (M03) — Schemas de postulaciones, contratos y calificaciones
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Postulaciones ──────────────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    job_offer_id: UUID
    cover_message: str | None = Field(None, max_length=500)
    proposed_rate: Decimal | None = Field(None, gt=0, lt=100_000)


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    job_offer_id: str
    worker_id: str
    cover_message: str | None
    proposed_rate: Decimal | None
    status: str
    created_at: datetime
    # info de la oferta (join)
    offer_title: str = ""
    employer_name: str = ""


# ── Contratos ─────────────────────────────────────────────────────────────────

class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    job_request_id: str
    worker_id: str
    employer_id: str
    status: str
    agreed_rate: Decimal | None
    rate_type: str | None
    start_date: date | None
    end_date: date | None
    final_amount: Decimal | None
    payment_method: str | None
    payment_confirmed: bool
    created_at: datetime


class ContractStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(CONFIRMED|IN_PROGRESS|COMPLETED|CANCELLED)$")
    cancelled_reason: str | None = Field(None, max_length=50)
    final_amount: Decimal | None = None
    payment_method: str | None = Field(None, max_length=30)


# ── Calificaciones ─────────────────────────────────────────────────────────────

class RatingCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    contract_id: UUID
    rated_id: UUID
    overall_score: float = Field(..., ge=1.0, le=5.0)
    quality_score: float | None = Field(None, ge=1.0, le=5.0)
    punctuality_score: float | None = Field(None, ge=1.0, le=5.0)
    communication_score: float | None = Field(None, ge=1.0, le=5.0)
    fairness_score: float | None = Field(None, ge=1.0, le=5.0)
    comment: str | None = Field(None, max_length=300)


class RatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    contract_id: str
    rater_id: str
    rated_id: str
    rater_role: str
    overall_score: float
    quality_score: float | None
    punctuality_score: float | None
    communication_score: float | None
    fairness_score: float | None
    comment: str | None
    sentiment: str | None
    created_at: datetime
