# RF: RF001-RF035, RNF001-RNF023
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine, init_db
from app.core.logging import configure_logging
from app.nlp.embeddings.generator import apply_local_dictionary, load_embedding_model

configure_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    apply_local_dictionary("")
    load_embedding_model()
    logger.info("app_started", version="0.2.0", environment=settings.ENVIRONMENT)
    yield
    await engine.dispose()
    logger.info("app_shutdown")


app = FastAPI(
    title="Sistema de Intermediacion Laboral DRTPE-Junin",
    version="0.1.0",
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

origins = (
    ["http://localhost:5173"]
    if settings.ENVIRONMENT == "development"
    else [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000, 2)
    response.headers["X-Process-Time"] = str(duration_ms)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", exc_info=True, path=str(request.url))
    detail = str(exc) if settings.ENVIRONMENT == "development" else "Error interno del servidor"
    return JSONResponse(status_code=500, content={"detail": detail})


app.include_router(api_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "sprint": 2,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["system"])
async def health_legacy():
    return {"status": "ok", "environment": settings.ENVIRONMENT, "version": "0.1.0"}
