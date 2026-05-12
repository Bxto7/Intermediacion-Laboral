# RF: RNF007, RNF008 — Rate limiting global por IP/usuario
import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = structlog.get_logger()

RATE_LIMIT_GLOBAL = 1000  # req/min por IP
RATE_LIMIT_AUTH = 10      # req/min por IP (login/register)
RATE_LIMIT_MATCHING = 30  # req/min por usuario (matching es pesado)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis) -> None:
        super().__init__(app)
        self.redis = redis

    async def dispatch(self, request: Request, call_next):
        ip = (request.headers.get("X-Forwarded-For", "") or "").split(",")[0].strip()
        if not ip:
            ip = request.client.host if request.client else "unknown"

        path = request.url.path
        minute = int(time.time() // 60)

        if "/auth/" in path:
            limit = RATE_LIMIT_AUTH
            key = f"rl:auth:{ip}:{minute}"
        elif "/match/" in path:
            limit = RATE_LIMIT_MATCHING
            user_id = request.headers.get("X-User-ID", ip)
            key = f"rl:match:{user_id}:{minute}"
        else:
            limit = RATE_LIMIT_GLOBAL
            key = f"rl:global:{ip}:{minute}"

        try:
            count = await self.redis.incr(key)
            await self.redis.expire(key, 120)
        except Exception:
            return await call_next(request)

        if count > limit:
            logger.warning("rate_limit_exceeded", key=key, count=count, limit=limit, path=path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas solicitudes. Intenta en un minuto."},
                headers={"Retry-After": "60"},
            )

        return await call_next(request)
