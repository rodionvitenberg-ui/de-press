"""Feed websocket and live story payload tests."""

from __future__ import annotations

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model

from apps.identity.services import Actor
from apps.identity.models import AnonymousSession
from apps.stories.services import delete_story, edit_story, hide_story, publish_story, unhide_story
from config.asgi import application

Account = get_user_model()


def _memory_layers(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }


@database_sync_to_async
def _session_for(author) -> str:
    from django.contrib.sessions.backends.db import SessionStore

    store = SessionStore()
    store["_auth_user_id"] = str(author.id)
    store["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
    store["_auth_user_hash"] = author.get_session_auth_hash()
    store.save()
    return store.session_key


@pytest.mark.django_db
def test_author_key_and_serialize_have_no_pulse():
    from apps.stories.realtime import author_key_for, serialize_story_live

    acc = Account.objects.create_user(email="k@ex.com", password="password123")
    story = publish_story(Actor(kind="account", account=acc), "тихо", topic="anxiety")
    assert author_key_for(story) == f"a:{acc.id}"
    payload = serialize_story_live(story)
    assert payload["id"] == str(story.id)
    assert payload["author_key"] == f"a:{acc.id}"
    assert payload["body"] == "тихо"
    assert "is_mine" not in payload
    assert "pulse" not in payload
    assert "pulse_count" not in payload


@pytest.mark.django_db
def test_author_key_for_anonymous_session():
    from apps.stories.realtime import author_key_for

    sess = AnonymousSession.objects.create()
    story = publish_story(Actor(kind="anonymous", session=sess), "гость")
    assert author_key_for(story) == f"s:{sess.id}"


@pytest.mark.django_db
def test_broadcast_unknown_type_is_noop(settings):
    from apps.stories.realtime import broadcast_story_event

    _memory_layers(settings)
    broadcast_story_event("story.nope")  # must not raise


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_anonymous_feed_socket_accepts_and_pongs(settings):
    _memory_layers(settings)
    communicator = WebsocketCommunicator(application, "/ws/feed/")
    connected, _ = await communicator.connect()
    assert connected is True
    await communicator.send_json_to({"type": "ping"})
    msg = await communicator.receive_json_from(timeout=5)
    assert msg["type"] == "pong"
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_anonymous_feed_socket_gets_publish(settings):
    _memory_layers(settings)
    communicator = WebsocketCommunicator(application, "/ws/feed/")
    connected, _ = await communicator.connect()
    assert connected is True

    acc = await database_sync_to_async(Account.objects.create_user)(
        email="pub@ex.com",
        password="password123",
    )
    await database_sync_to_async(publish_story)(
        Actor(kind="account", account=acc),
        "новая мысль",
    )
    event = await communicator.receive_json_from(timeout=5)
    assert event["type"] == "story.published"
    assert event["story"]["body"] == "новая мысль"
    assert event["story"]["author_key"].startswith("a:")
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_feed_socket_hide_and_delete(settings):
    _memory_layers(settings)
    communicator = WebsocketCommunicator(application, "/ws/feed/")
    connected, _ = await communicator.connect()
    assert connected is True

    acc = await database_sync_to_async(Account.objects.create_user)(
        email="mut@ex.com",
        password="password123",
    )
    actor = Actor(kind="account", account=acc)
    story = await database_sync_to_async(publish_story)(actor, "будет скрыто")
    published = await communicator.receive_json_from(timeout=5)
    assert published["type"] == "story.published"

    await database_sync_to_async(hide_story)(actor, story.id)
    hidden = await communicator.receive_json_from(timeout=5)
    assert hidden["type"] == "story.hidden"
    assert hidden["story"]["id"] == str(story.id)

    await database_sync_to_async(delete_story)(actor, story.id)
    deleted = await communicator.receive_json_from(timeout=5)
    assert deleted["type"] == "story.deleted"
    assert deleted["story_id"] == str(story.id)
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_feed_socket_edit_and_unhide(settings):
    _memory_layers(settings)
    communicator = WebsocketCommunicator(application, "/ws/feed/")
    connected, _ = await communicator.connect()
    assert connected is True
    acc = await database_sync_to_async(Account.objects.create_user)(
        email="edit@ex.com",
        password="password123",
    )
    actor = Actor(kind="account", account=acc)
    story = await database_sync_to_async(publish_story)(actor, "черновик")
    assert (await communicator.receive_json_from(timeout=5))["type"] == "story.published"
    await database_sync_to_async(edit_story)(actor, story.id, "правка")
    updated = await communicator.receive_json_from(timeout=5)
    assert updated["type"] == "story.updated"
    assert updated["story"]["body"] == "правка"
    await database_sync_to_async(hide_story)(actor, story.id)
    assert (await communicator.receive_json_from(timeout=5))["type"] == "story.hidden"
    await database_sync_to_async(unhide_story)(actor, story.id)
    shown = await communicator.receive_json_from(timeout=5)
    assert shown["type"] == "story.unhidden"
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_blocked_viewer_does_not_receive_author(settings):
    from apps.moderation.blocks import block_actor

    _memory_layers(settings)
    author = await database_sync_to_async(Account.objects.create_user)(
        email="blocked-author@ex.com",
        password="password123",
    )
    blocker = await database_sync_to_async(Account.objects.create_user)(
        email="blocker@ex.com",
        password="password123",
    )
    await database_sync_to_async(block_actor)(
        Actor(kind="account", account=blocker),
        target_account_id=author.id,
    )
    session_key = await _session_for(blocker)
    communicator = WebsocketCommunicator(
        application,
        "/ws/feed/",
        headers=[(b"cookie", f"sessionid={session_key}".encode())],
    )
    connected, _ = await communicator.connect()
    assert connected is True

    await database_sync_to_async(publish_story)(
        Actor(kind="account", account=author),
        "этого не должно быть видно",
    )
    assert await communicator.receive_nothing(timeout=0.5) is True
    await communicator.disconnect()
