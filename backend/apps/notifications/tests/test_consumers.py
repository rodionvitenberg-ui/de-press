"""WebSocket consumer tests for the notifications app."""

from __future__ import annotations

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model

from apps.identity.services import Actor
from apps.notifications.services import notify
from config.asgi import application

Account = get_user_model()


@database_sync_to_async
def _session_for(author) -> str:
    from django.contrib.sessions.backends.db import SessionStore

    store = SessionStore()
    store["_auth_user_id"] = str(author.id)
    store["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
    store["_auth_user_hash"] = author.get_session_auth_hash()
    store.save()
    return store.session_key


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_websocket_receives_live_notification(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }

    account = await database_sync_to_async(Account.objects.create_user)(
        email="live@ex.com",
        password="password123",
    )
    actor = Actor(kind="account", account=account)

    session_key = await _session_for(account)

    communicator = WebsocketCommunicator(
        application,
        "/ws/notifications/",
        headers=[(b"cookie", f"sessionid={session_key}".encode())],
    )
    connected, _ = await communicator.connect()
    assert connected is True

    snapshot = await communicator.receive_json_from(timeout=5)
    assert snapshot["type"] == "snapshot"
    assert snapshot["unread_count"] == 0

    await database_sync_to_async(notify)(
        actor,
        "message",
        {"dialogue_id": "00000000-0000-0000-0000-000000000002"},
    )

    event = await communicator.receive_json_from(timeout=5)
    assert event["type"] == "notification.new"
    assert event["notification"]["kind"] == "message"

    count_event = await communicator.receive_json_from(timeout=5)
    assert count_event["type"] == "unread_count"
    assert count_event["count"] == 1

    await communicator.send_json_to(
        {"type": "notifications.read", "id": event["notification"]["id"]}
    )
    read_event = await communicator.receive_json_from(timeout=5)
    assert read_event["type"] == "notification.read"
    count_after = await communicator.receive_json_from(timeout=5)
    assert count_after["type"] == "unread_count"
    assert count_after["count"] == 0

    await communicator.disconnect()