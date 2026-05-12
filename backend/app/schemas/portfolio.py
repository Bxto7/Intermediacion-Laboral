# RF: RF056-RF065
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PortfolioEntryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    period_start: date | None = None
    period_end: date | None = None
    client_rating: float | None = Field(None, ge=1.0, le=5.0)
    is_public: bool = True


class PortfolioEntryResponse(BaseModel):
    """Internal response — used only for authenticated worker endpoints."""

    model_config = ConfigDict(from_attributes=True)
    id: str
    worker_id: str
    title: str
    description: str
    extracted_skills: list[str]
    photos: list[str]
    period_start: date | None
    period_end: date | None
    client_rating: float | None
    is_public: bool
    created_at: datetime


class PublicPortfolioEntryResponse(BaseModel):
    """Public response — worker_id intentionally omitted (RNF001 / Sprint 3 audit).

    The public portfolio endpoint must use this schema so that internal
    UUIDs are never exposed to unauthenticated callers.
    """

    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str
    extracted_skills: list[str]
    photos: list[str]
    period_start: date | None
    period_end: date | None
    client_rating: float | None
    is_public: bool
    created_at: datetime


class PortfolioEntryUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=20, max_length=2000)
    period_start: date | None = None
    period_end: date | None = None
    client_rating: float | None = Field(None, ge=1.0, le=5.0)
    is_public: bool | None = None
