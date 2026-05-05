# RF: RF066-RF070
from pydantic import BaseModel


class ParsedCVResult(BaseModel):
    full_name: str | None = None
    full_name_confidence: float = 0.0
    email: str | None = None
    email_confidence: float = 0.0
    phone: str | None = None
    phone_confidence: float = 0.0
    education: list[dict] = []
    education_confidence: float = 0.0
    work_experiences: list[dict] = []
    work_experiences_confidence: float = 0.0
    skills: list[str] = []
    skills_confidence: float = 0.0
    raw_text_length: int = 0
    parse_warnings: list[str] = []
