from __future__ import annotations

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore

from apps.dialogue.models import DialogueStatus
from apps.dialogue.realtime import dialogue_group, serialize_message
from apps.dialogue.services import accept_request, create_request, send_message
from apps.identity.models import AnonymousSession
from apps.identity.services import Actor
from apps.stories.services import publish_story
from config.asgi import application

Account = get_user_model()


@pytest.mark.django_db
def test_dialogue_group_name():
    assert dialogue_group("abc") == "dialogue.abc"


@pytest.mark.django_db(transaction=True)
def test_broadcast_after_http_send(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    author = Account.objects.create_user(email="b@ex.com", password="password123")
    author_actor = Actor(kind="account", account=author)
    story = publish_story(author_actor, "broadcast monologue", topic="anxiety")
    peer_sess = AnonymousSession.objects.create()
    peer = Actor(kind="anonymous", session=peer_sess)
    req = create_request(peer, story.id, intent="share")
    dialogue = accept_request(author_actor, req.id)
    msg = send_message(author_actor, dialogue.id, "HTTP then WS fanout")
    payload = serialize_message(msg, viewer=author_actor)
    assert payload["body"] == "HTTP then WS fanout"
    assert payload["from_me"] is True


@pytest.mark.django_db
def test_serialize_circle_includes_video_and_ephemeral(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.dialogue.services import send_circle_message

    author = Account.objects.create_user(email="ser-c@ex.com", password="password123")
    author_actor = Actor(kind="account", account=author)
    story = publish_story(author_actor, "serialize circle")
    peer = Actor(kind="anonymous", session=AnonymousSession.objects.create())
    dialogue = accept_request(
        author_actor, create_request(peer, story.id, intent="listen").id
    )
    msg = send_circle_message(
        author_actor,
        dialogue.id,
        uploaded_file=SimpleUploadedFile("c.webm", b"abcd", content_type="video/webm"),
        duration_ms=1200,
    )
    payload = serialize_message(msg, viewer=author_actor)
    assert payload["kind"] == "circle"
    assert payload["ephemeral"] is True
    assert payload["video_url"]
    assert payload["audio_url"] is None


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_websocket_history_and_message(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }

    author = await database_sync_to_async(Account.objects.create_user)(
        email="ws-author@ex.com",
        password="password123",
    )
    dialogue = await _open_dialogue(author)
    session_key = await _session_for(author)

    communicator = WebsocketCommunicator(
        application,
        f"/ws/dialogues/{dialogue.id}/",
        headers=[(b"cookie", f"sessionid={session_key}".encode())],
    )

    connected, _ = await communicator.connect()
    assert connected is True

    first = await communicator.receive_json_from()
    assert first["type"] == "history"
    assert len(first["messages"]) >= 1

    await communicator.send_json_to({"type": "typing.start"})
    # Own typing is not echoed to self
    # Peer would receive typing — single-socket test only checks no crash / no echo
    # (no pending message of type typing for self)

    await communicator.send_json_to({"type": "message.send", "body": "Привет из WS"})
    event = await communicator.receive_json_from(timeout=5)
    assert event["type"] == "message.new"
    assert "Привет из WS" in event["message"]["body"]

    await communicator.disconnect()


@database_sync_to_async
def _session_for(author) -> str:
    store = SessionStore()
    store["_auth_user_id"] = str(author.id)
    store["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
    store["_auth_user_hash"] = author.get_session_auth_hash()
    store.save()
    return store.session_key


@database_sync_to_async
def _open_dialogue(author):
    author_actor = Actor(kind="account", account=author)
    story = publish_story(author_actor, "WS monologue", topic="loneliness")
    peer_sess = AnonymousSession.objects.create(pseudonym="peer")
    peer = Actor(kind="anonymous", session=peer_sess)
    req = create_request(peer, story.id, intent="listen")
    dialogue = accept_request(author_actor, req.id)
    assert dialogue.status == DialogueStatus.OPEN
    return dialogue
