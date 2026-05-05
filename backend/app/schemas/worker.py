from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import District, TradeCategory, WorkerType


class WorkerProfileCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    full_name: str = Field(..., min_length=2, max_length=100)
    dni: str = Field(..., pattern=r"^\d{8}$")
    phone: str | None = Field(None, pattern=r"^\+51 9\d{8}$")
    district: District
    trade_category: TradeCategory | None = None
    years_experience: int = Field(0, ge=0, le=50)
    worker_type: WorkerType


class WorkerProfileResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    id: UUID
    worker_type: WorkerType
    full_name: str
    district: District | None
    trade_category: TradeCategory | None
    years_experience: int
    avg_rating: float
    is_available: bool
    profile_completeness: int
    username: str | None = None
    bio: str | None = None
    job_title: str | None = None
    education_level: str | None = None
    created_at: datetime


class WorkerProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    full_name: str | None = Field(None, min_length=2, max_length=100)
    phone: str | None = Field(None, pattern=r"^\+51 9\d{8}$")
    district: District | None = None
    trade_category: TradeCategory | None = None
    years_experience: int | None = Field(None, ge=0, le=50)
    is_available: bool | None = None
    bio: str | None = Field(None, max_length=500)
    job_title: str | None = Field(None, max_length=100)
    username: str | None = Field(None, max_length=50)
    education_level: str | None = Field(None, max_length=50)


class CompletenessResponse(BaseModel):
    percentage: int
    missing_fields: list[str]
    next_action: str
