# RF: RNF007
import structlog
from redis.asyncio import ConnectionError, Redis
from redis.asyncio import from_url as redis_from_url

from app.core.config import settings

logger = structlog.get_logger()

_redis_client: Redis | None = None


def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis_from_url(
            settings.REDIS_URL,
            decode_responses=True,
            retry_on_error=[ConnectionError],
        )
    return _redis_client


async def is_token_blacklisted(token: str) -> bool:
    redis = get_redis()
    return await redis.exists(f"blacklist:{token}") > 0
