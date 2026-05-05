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


class PortfolioEntryUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=20, max_length=2000)
    period_start: date | None = None
    period_end: date | None = None
    client_rating: float | None = Field(None, ge=1.0, le=5.0)
    is_public: bool | None = None
