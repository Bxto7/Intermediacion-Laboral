# RF: RF041-RF055
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import District, WorkerType


class JobOfferCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=50, max_length=5000)
    required_skills: list[str] = Field(default_factory=list, max_length=20)
    preferred_skills: list[str] = Field(default_factory=list)
    district: District | None = None
    modality: Literal["presencial", "remoto", "hibrido"]
    salary_min: Decimal | None = Field(None, ge=0)
    salary_max: Decimal | None = Field(None, ge=0)
    worker_type_target: WorkerType | Literal["cualquiera"] = "cualquiera"
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_salary_range(self) -> "JobOfferCreate":
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_max <= self.salary_min:
                raise ValueError("salary_max debe ser mayor que salary_min")
        return self


class JobOfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    employer_id: str
    employer_name: str
    title: str
    description: str
    required_skills: list[str]
    preferred_skills: list[str]
    district: str | None
    modality: str
    salary_min: Decimal | None
    salary_max: Decimal | None
    worker_type_target: str
    is_active: bool
    expires_at: datetime | None
    views_count: int
    applications_count: int
    days_until_expiry: int | None
    created_at: datetime


class JobOfferUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str | None = Field(None, min_length=5, max_length=200)
    description: str | None = Field(None, min_length=50, max_length=5000)
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    district: District | None = None
    modality: Literal["presencial", "remoto", "hibrido"] | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    worker_type_target: WorkerType | Literal["cualquiera"] | None = None
    expires_at: datetime | None = None


class ApplicationCreate(BaseModel):
    job_offer_id: str
    cover_note: str | None = Field(None, max_length=500)


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    job_offer_id: str
    worker_id: str
    status: str
    match_score: Decimal | None
    cover_note: str | None
    applied_at: datetime
    job_title: str
    worker_name: str = ""
