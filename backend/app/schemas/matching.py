# RF: RF076-RF095 — Matching engine schemas
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MatchExplanation(BaseModel):
    matching_skills: list[str]
    missing_skills: list[str]
    district_note: str
    compatibility_label: str
    main_reason: str


class JobMatchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: UUID
    combined_score: float
    rank: int
    explanation: MatchExplanation


class MatchResponse(BaseModel):
    worker_id: UUID
    matches: list[JobMatchResult]
    total: int
