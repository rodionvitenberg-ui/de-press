"""Shared test helper to create a pending dialogue request."""

from __future__ import annotations

from apps.dialogue.services import create_request
from apps.identity.services import Actor
from apps.stories.models import Story


def create_reviewed_request(
    peer: Actor,
    story: Story,
    *,
    intent: str = "listen",
    note: str = "",
):
    """Create a request already visible in the author's inbox."""
    return create_request(peer, story.id, intent=intent, note=note)
