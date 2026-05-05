from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.common import TradeCategory, WorkerType


class OnboardingAnswers(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    is_first_job: bool
    is_trade_worker: bool
    trade_category: TradeCategory | None = None

    @model_validator(mode="after")
    def validate_trade_category(self) -> "OnboardingAnswers":
        if not self.is_first_job and self.is_trade_worker and self.trade_category is None:
            raise ValueError(
                "trade_category es obligatorio cuando is_trade_worker es True"
            )
        return self


class OnboardingResponse(BaseModel):
    worker_type: WorkerType
    worker_id: UUID
    next_step: str
    message: str


class OnboardingStatus(BaseModel):
    worker_type: WorkerType | None
    profile_completeness: int
    is_onboarded: bool
