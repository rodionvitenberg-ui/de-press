from __future__ import annotations

import pytest

from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor
from apps.moderation.models import Report, ReportReason, ReportStatus
from apps.moderation.services import submit_report
from apps.stories.services import publish_story


@pytest.mark.django_db
def test_submit_report_idempotent():
    author = Account.objects.create_user(email="auth@ex.com", password="password123")
    story = publish_story(Actor(kind="account", account=author), "Большая история.")

    session = AnonymousSession.objects.create()
    visitor = Actor(kind="anonymous", session=session)

    first = submit_report(
        visitor,
        story.id,
        reason=ReportReason.ABUSE,
        details="троллинг",
    )
    second = submit_report(
        visitor,
        story.id,
        reason=ReportReason.SPAM,
    )
    assert first.created is True
    assert second.created is False
    assert Report.objects.filter(story=story, status=ReportStatus.OPEN).count() == 1


@pytest.mark.django_db
def test_blocked_author_keys_for_account():
    from apps.moderation.blocks import block_actor, blocked_author_keys_for

    blocker = Account.objects.create_user(email="blk@ex.com", password="password123")
    target = Account.objects.create_user(email="tgt@ex.com", password="password123")
    actor = Actor(kind="account", account=blocker)
    block_actor(actor, target_account_id=target.id)
    keys = blocked_author_keys_for(actor)
    assert f"a:{target.id}" in keys
    empty = Actor(kind="anonymous", session=None)
    assert blocked_author_keys_for(empty) == set()
