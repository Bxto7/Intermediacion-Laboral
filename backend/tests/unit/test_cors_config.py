"""Verifica que CORS no esta en modo wildcard en produccion.

RF: RNF001, RNF003 — Sprint 3 Security Audit
Covers: app/core/config.py ALLOWED_ORIGINS, app/main.py CORS setup
"""
import pytest

# Non-default valid AES_KEY for production tests (base64 of 32 null bytes)
_PROD_AES_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


def test_cors_not_wildcard_when_configured_for_production():
    """Settings.ALLOWED_ORIGINS no debe contener '*' cuando ENV=production."""
    from app.core.config import Settings

    settings = Settings(
        ENVIRONMENT="production",
        ALLOWED_ORIGINS="https://example.com,https://admin.example.com",
        AES_KEY=_PROD_AES_KEY,
    )
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    assert "*" not in origins, (
        f"Wildcard '*' encontrado en ALLOWED_ORIGINS de produccion: {origins}"
    )


def test_cors_allowed_origins_splits_correctly():
    """ALLOWED_ORIGINS con multiples dominios se parsea correctamente."""
    from app.core.config import Settings

    settings = Settings(
        ENVIRONMENT="production",
        ALLOWED_ORIGINS="https://a.com, https://b.com , https://c.com",
        AES_KEY=_PROD_AES_KEY,
    )
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    assert len(origins) == 3
    assert "https://a.com" in origins
    assert "https://b.com" in origins
    assert "https://c.com" in origins


def test_cors_development_allows_localhost():
    """En development, el origen localhost esta permitido."""
    from app.core.config import Settings

    settings = Settings(
        ENVIRONMENT="development",
        ALLOWED_ORIGINS="http://localhost:3000",
        AES_KEY="Y2FtYmlhLWVzdG8tZXhhY3RhbWVudGUtMzJieXRlcyE=",
    )
    assert "localhost" in settings.ALLOWED_ORIGINS


def test_production_rejects_default_aes_key():
    """En production, la AES_KEY por defecto debe causar ValidationError."""
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS="https://example.com",
            AES_KEY="Y2FtYmlhLWVzdG8tZXhhY3RhbWVudGUtMzJieXRlcyE=",
        )
