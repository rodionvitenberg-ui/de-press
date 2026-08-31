from __future__ import annotations

import pytest

from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor
from apps.moderation.models import Report, ReportReason, ReportStatus
from apps.moderation.services import resolve_report, submit_message_report, submit_report
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


def _open_help_dialogue():
    from apps.dialogue.help import accept_help_request, create_help_request
    from apps.dialogue.services import send_message

    helper_acc = Account.objects.create_user(
        email="help-rep@ex.com", password="password123", is_helper=True
    )
    helper = Actor(kind="account", account=helper_acc)
    sess = AnonymousSession.objects.create()
    visitor = Actor(kind="anonymous", session=sess)
    req = create_help_request(visitor, note="мне тяжело")
    dialogue = accept_help_request(helper, req.id)
    msg = send_message(helper, dialogue.id, "я рядом")
    return helper, visitor, dialogue, msg


@pytest.mark.django_db
def test_submit_message_report_on_help_chat_without_story():
    helper, visitor, dialogue, msg = _open_help_dialogue()
    assert dialogue.story_id is None

    result = submit_message_report(
        visitor, msg.id, reason=ReportReason.ABUSE, details="плохо"
    )
    assert result.created is True
    assert result.report.story_id is None
    assert result.report.message_id == msg.id

    again = submit_message_report(visitor, msg.id, reason=ReportReason.SPAM)
    assert again.created is False
    assert (
        Report.objects.filter(
            message=msg, from_session=visitor.session, status=ReportStatus.OPEN
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_resolve_hidden_help_report_does_not_need_story():
    helper, visitor, dialogue, msg = _open_help_dialogue()
    submitted = submit_message_report(visitor, msg.id, reason=ReportReason.OTHER)
    resolved = resolve_report(
        submitted.report.id,
        decision="hide",
        reason=ReportReason.OTHER,
    )
    assert resolved.status == ReportStatus.RESOLVED_HIDDEN
    assert resolved.story_id is None
