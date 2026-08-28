from __future__ import annotations

from ninja import Router
from django.db import connection

router = Router(tags=["health"])


@router.get("/health")
def health(request):
    db_ok = False
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    redis_ok = False
    try:
        from config.redis import ping_redis

        redis_ok = ping_redis()
    except Exception:
        redis_ok = False

    channels_ok = False
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()
        if layer is not None:
            # InMemory and Redis both support group_send; treat presence as ok
            channels_ok = True
            # Optional lightweight probe for redis layer
            if hasattr(layer, "flush"):
                pass
    except Exception:
        channels_ok = False

    status = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "database": db_ok,
        "redis": redis_ok,
        "channels": channels_ok,
    }
