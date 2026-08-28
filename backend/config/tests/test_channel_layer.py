"""Channel-layer Redis host must not use redis-py 8's 5s socket timeout."""

from __future__ import annotations

from config.settings.base import _channel_redis_host


def test_channel_redis_host_disables_socket_read_timeout():
    host = _channel_redis_host("redis://127.0.0.1:6379/0")
    assert host["address"] == "redis://127.0.0.1:6379/0"
    assert host["socket_timeout"] is None
    assert host["socket_connect_timeout"] == 5


def test_redis_channel_layer_hosts_disable_socket_timeout():
    from config.settings import base as settings_base

    layer = settings_base.CHANNEL_LAYERS["default"]
    if layer["BACKEND"] != "channels_redis.core.RedisChannelLayer":
        import pytest

        pytest.skip("CHANNEL_LAYER is not redis")
    host = layer["CONFIG"]["hosts"][0]
    assert host["socket_timeout"] is None
    assert host["socket_connect_timeout"] == 5
