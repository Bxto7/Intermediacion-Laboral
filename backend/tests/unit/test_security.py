# RF: RF001-RF012, RNF001-RNF006
"""Unit tests for security utilities: hashing, JWT, AES encryption, RBAC."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


def test_hash_and_verify_password_success() -> None:
    from app.core.security import hash_password, verify_password

    plain = "SecurePass123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)


def test_wrong_password_fails() -> None:
    from app.core.security import hash_password, verify_password

    hashed = hash_password("correcta")
    assert not verify_password("incorrecta", hashed)


def test_hash_is_bcrypt_format() -> None:
    from app.core.security import hash_password

    hashed = hash_password("password123")
    assert hashed.startswith("$2b$")


def test_aes_encrypt_returns_bytes() -> None:
    from app.core.security import encrypt_field

    result = encrypt_field("12345678")
    assert isinstance(result, bytes)
    assert len(result) > 12  # nonce (12) + ciphertext


def test_aes_encrypt_decrypt_roundtrip() -> None:
    from app.core.security import decrypt_field, encrypt_field

    original = "12345678"
    encrypted = encrypt_field(original)
    assert decrypt_field(encrypted) == original


def test_aes_different_plaintexts_produce_different_ciphers() -> None:
    from app.core.security import encrypt_field

    # Same plaintext should produce different ciphertext due to random nonce
    c1 = encrypt_field("texto_igual")
    c2 = encrypt_field("texto_igual")
    assert c1 != c2


def test_aes_decrypt_each_nonce_independently() -> None:
    from app.core.security import decrypt_field, encrypt_field

    value = "12345678"
    enc1 = encrypt_field(value)
    enc2 = encrypt_field(value)
    assert decrypt_field(enc1) == decrypt_field(enc2) == value


def test_create_access_token_is_string() -> None:
    from app.core.security import create_access_token

    token = create_access_token({"sub": "user-123", "role": "worker"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token_is_string() -> None:
    from app.core.security import create_refresh_token

    token = create_refresh_token({"sub": "user-123", "role": "worker"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_access_token_contains_sub_jti_and_type() -> None:
    from pathlib import Path

    from jose import jwt

    from app.core.config import settings
    from app.core.security import create_access_token

    token = create_access_token({"sub": "user-123", "role": "worker"})
    public_key = Path(settings.JWT_PUBLIC_KEY_PATH).read_text()
    payload = jwt.decode(token, public_key, algorithms=["RS256"])
    assert payload["sub"] == "user-123"
    assert "jti" in payload
    assert payload["type"] == "access"


def test_refresh_token_has_type_refresh() -> None:
    from pathlib import Path

    from jose import jwt

    from app.core.config import settings
    from app.core.security import create_refresh_token

    token = create_refresh_token({"sub": "user-99", "role": "worker"})
    public_key = Path(settings.JWT_PUBLIC_KEY_PATH).read_text()
    payload = jwt.decode(token, public_key, algorithms=["RS256"])
    assert payload["type"] == "refresh"
    assert payload["sub"] == "user-99"


def test_expired_token_raises_401() -> None:
    import uuid as _uuid
    from pathlib import Path

    from jose import jwt

    from app.core.config import settings
    from app.core.security import verify_token

    payload = {
        "sub": "user-123",
        "role": "worker",
        "exp": datetime.now(tz=UTC) - timedelta(hours=1),
        "jti": str(_uuid.uuid4()),
        "type": "access",
    }
    private_key = Path(settings.JWT_PRIVATE_KEY_PATH).read_text()
    expired_token = jwt.encode(payload, private_key, algorithm="RS256")

    with patch(
        "app.core.security.is_token_blacklisted",
        new_callable=AsyncMock,
        return_value=False,
    ):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(verify_token(expired_token))
    assert exc_info.value.status_code == 401


def test_blacklisted_token_raises_401() -> None:
    from app.core.security import create_access_token, verify_token

    token = create_access_token({"sub": "user-1", "role": "worker"})

    with patch(
        "app.core.security.is_token_blacklisted",
        new_callable=AsyncMock,
        return_value=True,
    ):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(verify_token(token))
    assert exc_info.value.status_code == 401


def test_require_role_allows_correct_role() -> None:
    from app.core.security import UserRole, create_access_token, require_role

    token = create_access_token({"sub": "user-1", "role": "worker"})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    dep = require_role(UserRole.WORKER)

    _fake_redis = AsyncMock()
    _fake_redis.exists = AsyncMock(return_value=0)
    with patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock, return_value=False):
        with patch("app.core.security.get_redis", return_value=_fake_redis):
            result = asyncio.get_event_loop().run_until_complete(dep(credentials))
    assert result["sub"] == "user-1"
    assert result["role"] == "worker"


def test_require_role_blocks_wrong_role() -> None:
    from app.core.security import UserRole, create_access_token, require_role

    token = create_access_token({"sub": "user-1", "role": "worker"})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    dep = require_role(UserRole.ADMIN)

    _fake_redis = AsyncMock()
    _fake_redis.exists = AsyncMock(return_value=0)
    with patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock, return_value=False):
        with patch("app.core.security.get_redis", return_value=_fake_redis):
            with pytest.raises(HTTPException) as exc_info:
                asyncio.get_event_loop().run_until_complete(dep(credentials))
    assert exc_info.value.status_code == 403


def test_require_role_accepts_multiple_roles() -> None:
    from app.core.security import UserRole, create_access_token, require_role

    token = create_access_token({"sub": "user-1", "role": "employer"})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    dep = require_role(UserRole.WORKER, UserRole.EMPLOYER)

    _fake_redis = AsyncMock()
    _fake_redis.exists = AsyncMock(return_value=0)
    with patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock, return_value=False):
        with patch("app.core.security.get_redis", return_value=_fake_redis):
            result = asyncio.get_event_loop().run_until_complete(dep(credentials))
    assert result["role"] == "employer"


def test_user_role_enum_values() -> None:
    from app.core.security import UserRole

    assert UserRole.ADMIN.value == "admin"
    assert UserRole.EMPLOYER.value == "employer"
    assert UserRole.WORKER.value == "worker"
    assert UserRole.MODERATOR.value == "moderator"


def test_reset_password_blocks_all_sessions() -> None:
    from app.core.security import create_access_token, verify_token

    token = create_access_token({"sub": "blocked-user-1", "role": "worker"})

    async def _run():
        redis_mock = AsyncMock()
        redis_mock.exists = AsyncMock(side_effect=lambda key: 1 if "blacklist:user:blocked-user-1" in key else 0)
        with patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock, return_value=False):
            with patch("app.core.security.get_redis", return_value=redis_mock):
                with pytest.raises(HTTPException) as exc_info:
                    await verify_token(token)
        assert exc_info.value.status_code == 401

    asyncio.get_event_loop().run_until_complete(_run())


def test_get_client_ip_from_forwarded_for() -> None:
    from unittest.mock import MagicMock

    from app.core.rate_limit import get_client_ip

    request = MagicMock()
    request.headers = {"X-Forwarded-For": "1.2.3.4, 10.0.0.1"}
    request.client = None

    with patch("app.core.rate_limit.settings") as mock_settings:
        mock_settings.ENVIRONMENT = "production"
        ip = get_client_ip(request)
    assert ip == "1.2.3.4"


def test_rate_limit_blocks_after_threshold() -> None:
    from app.core.rate_limit import check_rate_limit

    async def _run():
        redis_mock = AsyncMock()
        call_count = 0

        async def fake_incr(key):
            nonlocal call_count
            call_count += 1
            return call_count

        async def fake_expire(key, ttl):
            pass

        async def fake_ttl(key):
            return 60

        redis_mock.incr = fake_incr
        redis_mock.expire = fake_expire
        redis_mock.ttl = fake_ttl

        for _ in range(3):
            await check_rate_limit("rl:test:unit", 3, 60, redis_mock)

        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit("rl:test:unit", 3, 60, redis_mock)
        assert exc_info.value.status_code == 429

    asyncio.get_event_loop().run_until_complete(_run())


def test_reset_password_invalidates_all_sessions() -> None:
    from app.core.security import create_access_token, verify_token

    token = create_access_token({"sub": "reset-user-99", "role": "worker"})

    async def _run():
        redis_mock = AsyncMock()
        redis_mock.exists = AsyncMock(
            side_effect=lambda key: 1 if "blacklist:user:reset-user-99" in key else 0
        )
        with patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock, return_value=False):
            with patch("app.core.security.get_redis", return_value=redis_mock):
                with pytest.raises(HTTPException) as exc_info:
                    await verify_token(token)
        assert exc_info.value.status_code == 401
        detail = exc_info.value.detail.lower()
        assert "invalidada" in detail or "sesion" in detail

    asyncio.get_event_loop().run_until_complete(_run())


def test_forgot_password_schema_validates_email() -> None:
    import pytest
    from pydantic import ValidationError

    from app.schemas.auth import ForgotPasswordRequest

    with pytest.raises(ValidationError):
        ForgotPasswordRequest(email="no-es-email")


# ── File validator (Sprint 3) ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_file_validator_rejects_wrong_mime() -> None:
    """Archivos que no son imagen deben ser rechazados."""
    from unittest.mock import MagicMock

    from app.utils.file_validator import validate_portfolio_photo

    file = MagicMock()
    file.read = AsyncMock(return_value=b"PK\x03\x04" + b"\x00" * 100)
    file.seek = AsyncMock()
    file.filename = "malicious.zip"
    file.content_type = "image/jpeg"

    import sys
    mock_magic = MagicMock()
    mock_magic.from_buffer.return_value = "application/zip"
    sys.modules["magic"] = mock_magic

    try:
        with pytest.raises(HTTPException) as exc_info:
            await validate_portfolio_photo(file)
        assert exc_info.value.status_code == 400
    finally:
        sys.modules.pop("magic", None)


@pytest.mark.asyncio
async def test_file_validator_rejects_oversized_file() -> None:
    """Archivos mayores a 5MB deben ser rechazados."""
    from unittest.mock import MagicMock

    from app.utils.file_validator import MAX_FILE_SIZE_BYTES, validate_portfolio_photo

    big_content = b"\xff\xd8\xff" + b"\x00" * (MAX_FILE_SIZE_BYTES + 1)
    file = MagicMock()
    file.read = AsyncMock(return_value=big_content)
    file.seek = AsyncMock()
    file.filename = "huge.jpg"
    file.content_type = "image/jpeg"

    import sys
    mock_magic = MagicMock()
    mock_magic.from_buffer.return_value = "image/jpeg"
    sys.modules["magic"] = mock_magic

    try:
        with pytest.raises(HTTPException) as exc_info:
            await validate_portfolio_photo(file)
        assert exc_info.value.status_code == 400
        assert "5 MB" in exc_info.value.detail
    finally:
        sys.modules.pop("magic", None)


@pytest.mark.asyncio
async def test_file_validator_accepts_valid_jpeg() -> None:
    """JPEG valido y dentro del tamano permitido debe pasar."""
    from unittest.mock import MagicMock

    from app.utils.file_validator import validate_portfolio_photo

    jpeg_content = b"\xff\xd8\xff\xe0" + b"\x00" * 1000
    file = MagicMock()
    file.read = AsyncMock(return_value=jpeg_content)
    file.seek = AsyncMock()
    file.filename = "photo.jpg"
    file.content_type = "image/jpeg"

    import sys
    mock_magic = MagicMock()
    mock_magic.from_buffer.return_value = "image/jpeg"
    sys.modules["magic"] = mock_magic

    try:
        result = await validate_portfolio_photo(file)
        assert result == jpeg_content
    finally:
        sys.modules.pop("magic", None)


@pytest.mark.asyncio
async def test_file_validator_fallback_without_magic() -> None:
    """Sin python-magic, usa content_type del header."""
    from unittest.mock import MagicMock

    from app.utils.file_validator import validate_portfolio_photo

    png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    file = MagicMock()
    file.read = AsyncMock(return_value=png_content)
    file.seek = AsyncMock()
    file.filename = "photo.png"
    file.content_type = "image/png"

    import sys
    # Remove magic from modules to simulate ImportError path
    original = sys.modules.get("magic")
    sys.modules["magic"] = None  # type: ignore

    try:
        result = await validate_portfolio_photo(file)
        assert result == png_content
    finally:
        if original is None:
            sys.modules.pop("magic", None)
        else:
            sys.modules["magic"] = original


# ── Cold start resolve_cold_start ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_cold_start_primer_empleo() -> None:
    """resolve_cold_start para PRIMER_EMPLEO genera embedding."""
    from unittest.mock import AsyncMock, MagicMock

    from app.ml.cold_start.resolver import resolve_cold_start

    worker = MagicMock()
    worker.id = "worker-cold-primer"
    worker.worker_type = "primer_empleo"
    worker.district = "Huancayo"
    worker.embedding = None

    wizard = MagicMock()
    wizard.extracted_skills = ["responsabilidad"]
    wizard.answers = {"job_interests": "comercio"}

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = wizard

    db = AsyncMock()
    db.execute.return_value = mock_result

    with patch("app.ml.cold_start.resolver.generate_embedding_sync", return_value=[0.1] * 384):
        result = await resolve_cold_start(worker, db)

    assert result.embedding == [0.1] * 384


@pytest.mark.asyncio
async def test_resolve_cold_start_oficio() -> None:
    """resolve_cold_start para OFICIO genera embedding desde portfolio."""
    from unittest.mock import AsyncMock, MagicMock

    from app.ml.cold_start.resolver import resolve_cold_start

    worker = MagicMock()
    worker.id = "worker-cold-oficio"
    worker.worker_type = "oficio"
    worker.trade_category = "Carpinteria"
    worker.district = "El Tambo"
    worker.years_experience = 5
    worker.embedding = None

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    db = AsyncMock()
    db.execute.return_value = mock_result

    with patch("app.ml.cold_start.resolver.generate_embedding_sync", return_value=[0.2] * 384):
        result = await resolve_cold_start(worker, db)

    assert result.embedding == [0.2] * 384


@pytest.mark.asyncio
async def test_resolve_cold_start_experiencia() -> None:
    """resolve_cold_start para EXPERIENCIA genera embedding."""
    from unittest.mock import AsyncMock, MagicMock

    from app.ml.cold_start.resolver import resolve_cold_start

    worker = MagicMock()
    worker.id = "worker-cold-exp"
    worker.worker_type = "experiencia"
    worker.bio = "Profesional contable"
    worker.job_title = "Contador"
    worker.years_experience = 4
    worker.district = "Chilca"
    worker.embedding = None

    db = AsyncMock()

    with patch("app.ml.cold_start.resolver.generate_embedding_sync", return_value=[0.3] * 384):
        result = await resolve_cold_start(worker, db)

    assert result.embedding == [0.3] * 384
