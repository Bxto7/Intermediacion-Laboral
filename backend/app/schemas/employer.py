# RF: RF036-RF040
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import District


class EmployerProfileCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    company_name: str = Field(..., min_length=2, max_length=255)
    ruc: str = Field(..., description="11 digitos numericos")
    contact_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., description="+51 9XXXXXXXX")
    district: District
    sector: str | None = Field(None, max_length=100)

    @field_validator("ruc")
    @classmethod
    def validate_ruc(cls, v: str) -> str:
        if not re.fullmatch(r"\d{11}", v):
            raise ValueError("RUC debe tener exactamente 11 digitos numericos")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.fullmatch(r"\+51\s?9\d{8}", v):
            raise ValueError("Telefono debe tener formato +51 9XXXXXXXX")
        return v


class EmployerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    company_name: str
    district: str | None
    sector: str | None
    is_verified: bool
    created_at: datetime


class EmployerProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    company_name: str | None = Field(None, min_length=2, max_length=255)
    contact_name: str | None = Field(None, min_length=2, max_length=100)
    phone: str | None = None
    district: District | None = None
    sector: str | None = Field(None, max_length=100)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.fullmatch(r"\+51\s?9\d{8}", v):
            raise ValueError("Telefono debe tener formato +51 9XXXXXXXX")
        return v
