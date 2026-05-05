# RF: RNF007, RNF008
import structlog
from fastapi import HTTPException, Request, status

from app.core.config import settings

logger = structlog.get_logger()


def get_client_ip(request: Request) -> str:
    if settings.ENVIRONMENT == "production":
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(key: str, limit: int, window_seconds: int, redis) -> None:
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window_seconds)
    if count > limit:
        ttl = await redis.ttl(key)
        retry_after = max(ttl, 1)
        logger.warning("rate_limit_exceeded", key=key, count=count, limit=limit)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intenta mas tarde.",
            headers={"Retry-After": str(retry_after)},
        )
