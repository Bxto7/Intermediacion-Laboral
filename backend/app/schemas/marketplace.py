# RF: RF118-RF125 (M07) — Schemas del marketplace de servicios de oficio
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServiceListingCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    trade_category: str = Field(..., min_length=2, max_length=50)
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    districts: list[str] = Field(default_factory=list)
    price_reference: Decimal | None = Field(None, gt=0, lt=10_000)
    price_unit: str | None = Field(None, pattern="^(hora|proyecto|dia)$")
    availability: str | None = Field(None, pattern="^(inmediata|semana|mes)$")


class ServiceListingUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(None, min_length=5, max_length=200)
    description: str | None = Field(None, min_length=10, max_length=2000)
    districts: list[str] | None = None
    price_reference: Decimal | None = None
    price_unit: str | None = Field(None, pattern="^(hora|proyecto|dia)$")
    availability: str | None = Field(None, pattern="^(inmediata|semana|mes)$")
    is_active: bool | None = None


class ServiceListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    worker_id: str
    trade_category: str
    title: str
    description: str
    enriched_keywords: list[str]
    districts: list[str]
    price_reference: Decimal | None
    price_unit: str | None
    availability: str | None
    is_active: bool
    views_count: int
    created_at: datetime
    # campos del worker (joins)
    worker_name: str = ""
    worker_district: str = ""
    worker_avg_rating: float = 0.0
    worker_years_experience: int = 0
    worker_username: str | None = None
    # score semántico (solo en búsqueda)
    relevance_score: float | None = None


class MarketplaceSearchParams(BaseModel):
    query: str | None = Field(None, max_length=300)
    districts: list[str] | None = None
    trade_category: str | None = None
    availability: str | None = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
