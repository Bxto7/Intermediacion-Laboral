# RF: RNF001, RNF018
import base64
from typing import Literal

import structlog
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger()

# base64.b64encode(b"cambia-esto-exactamente-32bytes!") — dev placeholder only
_DEFAULT_AES_KEY_B64 = "Y2FtYmlhLWVzdG8tZXhhY3RhbWVudGUtMzJieXRlcyE="


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/intermediacion_laboral"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_ALGORITHM: Literal["RS256"] = "RS256"
    JWT_PRIVATE_KEY_PATH: str = "keys/private.pem"
    JWT_PUBLIC_KEY_PATH: str = "keys/public.pem"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AES_KEY: str = _DEFAULT_AES_KEY_B64
    BCRYPT_COST: int = 12
    GCS_BUCKET_NAME: str = "intermediacion-laboral-dev"
    ENVIRONMENT: Literal["development", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # Extended settings kept for compatibility
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIM: int = 384
    MATCHING_ALPHA: float = 0.5
    MATCHING_BETA: float = 0.3
    MATCHING_GAMMA: float = 0.2
    TOP_K_DEFAULT: int = 10
    SIMILARITY_THRESHOLD: float = 0.3
    MIN_PROFILE_COMPLETENESS: int = 60

    @model_validator(mode="after")
    def validate_aes_key(self) -> "Settings":
        try:
            decoded = base64.b64decode(self.AES_KEY)
        except Exception as exc:
            raise ValueError("AES_KEY must be a valid base64-encoded string") from exc
        if len(decoded) != 32:
            raise ValueError(
                f"AES_KEY must decode to exactly 32 bytes, "
                f"got {len(decoded)} bytes after base64 decoding"
            )
        if self.ENVIRONMENT == "production" and self.AES_KEY == _DEFAULT_AES_KEY_B64:
            raise ValueError("AES_KEY must not use the default placeholder in production")
        return self


settings = Settings()
