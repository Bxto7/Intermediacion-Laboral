from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.employers import router as employers_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.nlp import router as nlp_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.wizard import router as wizard_router
from app.api.v1.workers import router as workers_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(workers_router)
api_router.include_router(employers_router)
api_router.include_router(jobs_router)
api_router.include_router(nlp_router)
api_router.include_router(wizard_router)
api_router.include_router(portfolio_router)


@api_router.get("/ping", tags=["system"])
async def ping():
    return {"message": "pong", "sprint": 2}
