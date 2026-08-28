"""Redis connection helpers (cache / future channel layer)."""

from __future__ import annotations

from functools import lru_cache

import redis
from django.conf import settings


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    """Return a shared Redis client for the configured REDIS_URL."""
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def ping_redis() -> bool:
    """Return True if Redis responds to PING."""
    try:
        return bool(get_redis_client().ping())
    except redis.RedisError:
        return False
