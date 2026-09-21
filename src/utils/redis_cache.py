"""Redis cache for LLM results (MedDRA codes, WHO Drug codes)."""
import json
import redis.asyncio as redis
import structlog

from src.config import settings


logger = structlog.get_logger()

_pool: redis.Redis | None = None


async def _get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
        )
    return _pool


async def get_cache(key: str) -> dict | str | None:
    """Get a cached value from Redis."""
    r = await _get_redis()
    value = await r.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


async def set_cache(key: str, value, ttl: int = 86400):
    """Set a cached value in Redis with TTL."""
    r = await _get_redis()
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    await r.set(key, value, ex=ttl)   