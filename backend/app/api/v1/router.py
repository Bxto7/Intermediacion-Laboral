from fastapi import APIRouter

from app.api.v1.admin import admin_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.applications import router as applications_router
from app.api.v1.auth import router as auth_router
from app.api.v1.contracts import router as contracts_router
from app.api.v1.cv import router as cv_router
from app.api.v1.employers import router as employers_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.marketplace import router as marketplace_router
from app.api.v1.matching import router as matching_router
from app.api.v1.nlp import router as nlp_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.surveys import router as surveys_router
from app.api.v1.wizard import router as wizard_router
from app.api.v1.workers import router as workers_router
from app.api.v1.ws_notifications import router as ws_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(workers_router)
api_router.include_router(employers_router)
api_router.include_router(jobs_router)
api_router.include_router(nlp_router)
api_router.include_router(wizard_router)
api_router.include_router(portfolio_router)
api_router.include_router(cv_router)
api_router.include_router(alerts_router)
api_router.include_router(matching_router)
api_router.include_router(marketplace_router)
api_router.include_router(applications_router)
api_router.include_router(contracts_router)
api_router.include_router(ws_router)
api_router.include_router(admin_router)
api_router.include_router(surveys_router)


@api_router.get("/ping", tags=["system"])
async def ping():
    return {"message": "pong", "sprint": 5}
