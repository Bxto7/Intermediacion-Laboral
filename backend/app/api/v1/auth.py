# RF: RF001-RF012, RNF001-RNF006
import time
import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import check_rate_limit, get_client_ip
from app.core.redis_client import get_redis
from app.core.security import (
    UserRole,
    create_access_token,
    create_refresh_token,
    hash_password,
    invalidate_token,
    require_role,
    verify_password,
    verify_token,
)
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.tasks.notifications import send_reset_email

router = APIRouter(prefix="/auth", tags=["Autenticacion"])
logger = structlog.get_logger()

RATE_LIMIT_REGISTER = 10
RATE_LIMIT_LOGIN = 20
RATE_LIMIT_FORGOT = 5


@router.post("/register", response_model=TokenResponse)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    start = time.monotonic()
    redis = get_redis()
    ip = get_client_ip(request)
    await check_rate_limit(f"rl:register:{ip}", RATE_LIMIT_REGISTER, 3600, redis)

    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role.value,
    )
    db.add(user)
    await db.flush()

    audit = AuditLog(
        user_id=user.id,
        action="user_registered",
        ip_address=ip,
        details={"role": body.role.value},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(user)

    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info(
        "user_registered",
        user_id=str(user.id),
        ip=ip,
        duration_ms=round((time.monotonic() - start) * 1000, 2),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    start = time.monotonic()
    redis = get_redis()
    ip = get_client_ip(request)
    await check_rate_limit(f"rl:login:{ip}", RATE_LIMIT_LOGIN, 3600, redis)

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.is_active or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
        )

    audit = AuditLog(
        user_id=user.id,
        action="user_login",
        ip_address=ip,
    )
    db.add(audit)
    await db.commit()

    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info(
        "user_login",
        user_id=str(user.id),
        ip=ip,
        duration_ms=round((time.monotonic() - start) * 1000, 2),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(body: RefreshRequest) -> TokenResponse:
    payload = await verify_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de tipo incorrecto",
        )
    jti = payload.get("jti")
    exp = payload.get("exp", 0)
    remaining = max(0, exp - int(datetime.now(tz=UTC).timestamp()))
    if jti:
        await invalidate_token(jti, remaining)

    token_data = {"sub": payload["sub"], "role": payload["role"]}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    payload: dict = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.EMPLOYER,
            UserRole.WORKER,
            UserRole.MODERATOR,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    jti = payload.get("jti")
    exp = payload.get("exp", 0)
    remaining = max(0, exp - int(datetime.now(tz=UTC).timestamp()))
    if jti:
        await invalidate_token(jti, remaining)

    audit = AuditLog(
        user_id=payload.get("sub"),
        action="user_logout",
        ip_address=get_client_ip(request),
    )
    db.add(audit)
    await db.commit()

    logger.info("user_logout", user_id=payload.get("sub"))
    return MessageResponse(message="Sesion cerrada correctamente")


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    payload: dict = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.EMPLOYER,
            UserRole.WORKER,
            UserRole.MODERATOR,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
        
    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    body: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    redis = get_redis()
    user_id = await redis.get(f"email_verify:{body.token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido o expirado",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.email_verified = True
        await db.commit()

    await redis.delete(f"email_verify:{body.token}")
    return MessageResponse(message="Email verificado correctamente")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    redis = get_redis()
    ip = get_client_ip(request)
    await check_rate_limit(f"rl:forgot:{ip}", RATE_LIMIT_FORGOT, 3600, redis)

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user:
        token = str(uuid.uuid4())
        await redis.setex(f"pwd_reset:{token}", 3600, str(user.id))
        send_reset_email.delay(str(user.id), token)

    return MessageResponse(
        message="Si el email existe, recibiras un enlace de recuperacion"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    from app.core.config import settings

    redis = get_redis()
    user_id = await redis.get(f"pwd_reset:{body.token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido o expirado",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.hashed_password = hash_password(body.new_password)
        await db.commit()

    await redis.delete(f"pwd_reset:{body.token}")
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await redis.setex(f"blacklist:user:{user_id}", ttl, "1")

    return MessageResponse(message="Contrasena actualizada correctamente")
