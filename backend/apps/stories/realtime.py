"""Broadcast public story events to the shared feed channel group."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings

from apps.stories.models import Story


def audio_url_for(story: Story) -> str | None:
    if not story.audio:
        return None
    try:
        url = story.audio.url
    except ValueError:
        return None
    media_base = getattr(settings, "MEDIA_URL", "/media/")
    if url.startswith("http"):
        return url
    if url.startswith("/"):
        return url
    return f"{media_base.rstrip('/')}/{url.lstrip('/')}"

FEED_GROUP = "feed.public"

LIVE_EVENT_TYPES = frozenset(
    {
        "story.published",
        "story.updated",
        "story.hidden",
        "story.unhidden",
        "story.deleted",
        "story.commented",
    }
)


def identity_key(*, account_id=None, session_id=None) -> str:
    if account_id:
        return f"a:{account_id}"
    if session_id:
        return f"s:{session_id}"
    return ""


def author_key_for(story: Story) -> str:
    return identity_key(
        account_id=story.author_account_id,
        session_id=story.author_session_id,
    )


def serialize_story_live(story: Story) -> dict[str, Any]:
    return {
        "id": str(story.id),
        "body": story.body,
        "topic": story.topic,
        "pseudonym": story.pseudonym_snapshot,
        "published_at": story.published_at.isoformat() if story.published_at else None,
        "status": story.status,
        "author_key": author_key_for(story),
        "parent_id": str(story.parent_id) if story.parent_id else None,
        "audio_url": audio_url_for(story),
        "duration_ms": story.duration_ms,
    }


def broadcast_story_event(
    event_type: str,
    *,
    story: Story | None = None,
    story_id: UUID | str | None = None,
    author_key: str | None = None,
    post_id: str | None = None,
) -> None:
    if event_type not in LIVE_EVENT_TYPES:
        return
    layer = get_channel_layer()
    if layer is None:
        return
    if event_type == "story.deleted":
        payload = {
            "story_id": str(story_id or (story.id if story is not None else "")),
            "author_key": author_key or (author_key_for(story) if story is not None else ""),
        }
    else:
        if story is None:
            return
        payload = serialize_story_live(story)
        if event_type == "story.commented":
            payload["post_id"] = str(post_id or story.parent_id or "")
    async_to_sync(layer.group_send)(
        FEED_GROUP,
        {"type": "story.event", "event_type": event_type, "payload": payload},
    )
