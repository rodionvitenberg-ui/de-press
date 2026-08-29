"""Shared test helpers for dialogue review flow."""

from __future__ import annotations

from uuid import uuid4

from apps.dialogue.services import approve_dialogue_request, create_request
from apps.identity.models import Account
from apps.identity.services import Actor
from apps.stories.models import Story


def helper_actor() -> Actor:
    acc = Account.objects.create_user(
        email=f"rev-{uuid4().hex[:10]}@ex.com",
        password="password123",
        is_helper=True,
        is_on_duty=True,
    )
    return Actor(kind="account", account=acc)


def create_reviewed_request(
    peer: Actor,
    story: Story,
    *,
    intent: str = "listen",
    note: str = "",
):
    helper = helper_actor()
    req = create_request(peer, story.id, intent=intent, note=note)
    approve_dialogue_request(helper, req.id)
    req.refresh_from_db()
    return req
