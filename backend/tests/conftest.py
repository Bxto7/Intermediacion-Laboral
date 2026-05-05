"""
Test configuration for the Sistema de Intermediacion Laboral backend.

Uses SQLite in-memory instead of PostgreSQL so tests run without external services.
Patches:
- SQLAlchemy PostgreSQL-specific types (JSONB, BYTEA) -> generic equivalents
- pgvector Vector columns -> FetchedValue (no-op for schema creation)
- server_default text expressions (gen_random_uuid, now()) -> FetchedValue / Python defaults
- get_redis() -> FakeAsyncRedis
- init_db() -> no-op (skips CREATE EXTENSION vector)
- configure_logging() -> no-op (keeps test-safe structlog config)
"""

from __future__ import annotations

# ── 1. Structlog must be configured with stdlib factory BEFORE app imports ──────
import logging

import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),  # stdlib logger has .name
    cache_logger_on_first_use=True,
)

# ── 2. Patch configure_logging to preserve our test config ──────────────────────
import app.core.logging as _app_logging

_app_logging.configure_logging = lambda: None  # type: ignore[assignment]

# ── 2b. Patch Celery tasks to avoid broker connections in tests ──────────────────
from unittest.mock import MagicMock as _MagicMock

import app.tasks.notifications as _notifications

_notifications.send_reset_email = _MagicMock()  # type: ignore[assignment]
_notifications.send_reset_email.delay = _MagicMock(return_value=None)

# ── 3. Patch PostgreSQL dialect types before any model imports ───────────────────
import sqlalchemy as _sa
from sqlalchemy.dialects import postgresql as _pg

_pg.JSONB = _sa.JSON  # type: ignore[assignment]
_pg.BYTEA = _sa.LargeBinary  # type: ignore[assignment]

# ── 4. Now it's safe to import app modules ───────────────────────────────────────
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import fakeredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — registers all ORM mappers
from app.core.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ── SQLite compatibility helpers ─────────────────────────────────────────────────

def _patch_metadata_for_sqlite(metadata: _sa.MetaData) -> None:
    """Replace PostgreSQL server_default expressions with FetchedValue.

    SQLite doesn't support gen_random_uuid() or now(), so we replace them
    with FetchedValue() which tells SQLAlchemy the DB "might" provide a value
    but doesn't generate any SQL for it. Python-side defaults are set via the
    before_insert event listener below.
    """
    for table in metadata.tables.values():
        for col in table.columns:
            if col.server_default is not None:
                sd_arg = col.server_default.arg
                if isinstance(sd_arg, _sa.sql.elements.TextClause):
                    col.server_default = _sa.FetchedValue()


def _set_defaults_before_insert(
    mapper: object, connection: object, target: object
) -> None:
    """SQLAlchemy before_insert event: generate Python-side UUID and timestamps.

    Called automatically before every INSERT across all mapped models.
    """
    if hasattr(target, "id") and target.id is None:
        target.id = str(uuid.uuid4())
    now = datetime.now(tz=UTC)
    for attr in ("created_at", "updated_at", "last_saved_at", "generated_at", "applied_at"):
        if hasattr(target, attr) and getattr(target, attr) is None:
            setattr(target, attr, now)


# Apply SQLite patches once at module load
_patch_metadata_for_sqlite(Base.metadata)
for _mapper in Base.registry.mappers:
    event.listen(_mapper, "before_insert", _set_defaults_before_insert)


# ── Session-scoped engine (shared across all tests) ──────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Single SQLite in-memory engine for the entire test session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


# ── Per-test DB session with rollback isolation ──────────────────────────────────

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated async session that rolls back after each test."""
    session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
        await session.rollback()


# ── Per-test fake Redis (resets between tests) ───────────────────────────────────

@pytest_asyncio.fixture
async def fake_redis():
    """FakeAsyncRedis — fresh instance per test so state never leaks."""
    redis = fakeredis.FakeAsyncRedis(decode_responses=True)
    yield redis
    await redis.flushall()
    await redis.aclose()


# ── Table cleanup between tests ───────────────────────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db(test_engine) -> AsyncGenerator[None, None]:
    """Truncate all tables after each test so integration tests are isolated.

    SQLite doesn't support TRUNCATE — we use DELETE instead.
    """
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


# ── HTTP test client with overridden DB and Redis ────────────────────────────────

@pytest_asyncio.fixture
async def client(
    fake_redis: fakeredis.FakeAsyncRedis,
    test_engine,
) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient backed by SQLite engine and fake Redis.

    Each test gets a fresh HTTP client. The cleanup_db autouse fixture
    ensures tables are empty at the start of every test.
    """
    from app.main import app

    # Session factory pointing at the shared in-memory engine
    session_maker = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch("app.core.redis_client._redis_client", fake_redis),
        patch("app.core.security.get_redis", return_value=fake_redis),
        patch("app.api.v1.auth.get_redis", return_value=fake_redis),
        patch("app.core.database.init_db", new_callable=AsyncMock),
        patch("app.api.v1.auth.send_reset_email"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


# ── Convenience data fixtures ────────────────────────────────────────────────────

@pytest.fixture
def worker_registration_payload() -> dict:
    """Standard worker registration payload."""
    return {
        "email": "trabajador@example.com",
        "password": "TestPass1!",
        "role": "worker",
    }


@pytest.fixture
def employer_registration_payload() -> dict:
    """Standard employer registration payload."""
    return {
        "email": "empleador@example.com",
        "password": "TestPass1!",
        "role": "employer",
    }
