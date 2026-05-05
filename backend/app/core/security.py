# RF: RF001-RF012, RNF001-RNF006
import base64
import os
import uuid
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path

import bcrypt
import structlog
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.core.redis_client import get_redis

logger = structlog.get_logger()

security_scheme = HTTPBearer()


class UserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYER = "employer"
    WORKER = "worker"
    MODERATOR = "moderator"


def _ensure_rsa_keys() -> None:
    private_key_path = Path(settings.JWT_PRIVATE_KEY_PATH)
    public_key_path = Path(settings.JWT_PUBLIC_KEY_PATH)

    if not private_key_path.exists() or not public_key_path.exists():
        private_key_path.parent.mkdir(parents=True, exist_ok=True)
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        private_key_path.write_bytes(private_pem)
        public_key_path.write_bytes(public_pem)
        logger.info("rsa_keys_generated", private_path=str(private_key_path))


_ensure_rsa_keys()


def _load_private_key() -> str:
    return Path(settings.JWT_PRIVATE_KEY_PATH).read_text()


def _load_public_key() -> str:
    return Path(settings.JWT_PUBLIC_KEY_PATH).read_text()


def _get_aes_key() -> bytes:
    return base64.b64decode(settings.AES_KEY)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=settings.BCRYPT_COST)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def encrypt_field(value: str) -> bytes:
    aesgcm = AESGCM(_get_aes_key())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_field(value: bytes) -> str:
    aesgcm = AESGCM(_get_aes_key())
    nonce = value[:12]
    ciphertext = value[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(tz=UTC) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload["jti"] = str(uuid.uuid4())
    payload["type"] = "access"
    return jwt.encode(payload, _load_private_key(), algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(tz=UTC) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload["jti"] = str(uuid.uuid4())
    payload["type"] = "refresh"
    return jwt.encode(payload, _load_private_key(), algorithm=settings.JWT_ALGORITHM)


async def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, _load_public_key(), algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
        ) from exc

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revocado",
        )

    user_id = payload.get("sub")
    if user_id:
        redis = get_redis()
        if await redis.exists(f"blacklist:user:{user_id}") > 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesion invalidada, vuelve a iniciar sesion",
            )

    return payload


async def invalidate_token(jti: str, expires_in_seconds: int) -> None:
    redis = get_redis()
    await redis.setex(f"blacklist:{jti}", expires_in_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    redis = get_redis()
    return await redis.exists(f"blacklist:{jti}") > 0


def require_role(*roles: UserRole):
    async def _dependency(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    ) -> dict:
        payload = await verify_token(credentials.credentials)
        token_role = payload.get("role")
        if token_role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a este recurso",
            )
        return payload

    return _dependency
