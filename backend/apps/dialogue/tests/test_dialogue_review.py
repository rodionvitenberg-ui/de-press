from __future__ import annotations

import pytest

from apps.dialogue.models import DialogueRequestStatus
from apps.dialogue.services import (
    DialogueError,
    accept_request,
    approve_dialogue_request,
    create_request,
    list_inbox,
    list_review_inbox,
    reject_dialogue_request,
)
from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor
from apps.notifications.models import Notification, NotificationKind
from apps.stories.services import publish_story


@pytest.mark.django_db
def test_create_request_awaits_helper_not_author():
    helper_acc = Account.objects.create_user(
        email="revh@ex.com", password="password123", is_helper=True
    )
    helper = Actor(kind="account", account=helper_acc)
    author_acc = Account.objects.create_user(
        email="reva@ex.com", password="password123"
    )
    author = Actor(kind="account", account=author_acc)
    story = publish_story(author, "Мне нужно, чтобы меня услышали.")
    peer = Actor(kind="anonymous", session=AnonymousSession.objects.create())

    req = create_request(peer, story.id, intent="listen", note="я рядом")
    assert req.status == DialogueRequestStatus.AWAITING_HELPER
    assert list_inbox(author) == []
    assert list_review_inbox(helper)[0].id == req.id
    assert Notification.objects.filter(
        kind=NotificationKind.DIALOGUE_REQUEST_REVIEW,
        recipient_account=helper_acc,
    ).exists()
    assert not Notification.objects.filter(
        kind=NotificationKind.DIALOGUE_REQUEST,
        recipient_account=author_acc,
    ).exists()

    with pytest.raises(DialogueError):
        accept_request(author, req.id)

    approved = approve_dialogue_request(helper, req.id)
    assert approved.status == DialogueRequestStatus.PENDING
    assert list_review_inbox(helper) == []
    assert list_inbox(author)[0].id == req.id
    assert Notification.objects.filter(
        kind=NotificationKind.DIALOGUE_REQUEST,
        recipient_account=author_acc,
    ).exists()

    dialogue = accept_request(author, req.id)
    assert dialogue.source == "request"


@pytest.mark.django_db
def test_helper_reject_hides_from_author():
    helper_acc = Account.objects.create_user(
        email="rejh@ex.com", password="password123", is_helper=True
    )
    helper = Actor(kind="account", account=helper_acc)
    author = Actor(
        kind="account",
        account=Account.objects.create_user(
            email="reja@ex.com", password="password123"
        ),
    )
    story = publish_story(author, "тихо")
    peer = Actor(kind="anonymous", session=AnonymousSession.objects.create())
    req = create_request(peer, story.id, intent="listen")
    reject_dialogue_request(helper, req.id)
    req.refresh_from_db()
    assert req.status == DialogueRequestStatus.DECLINED
    assert list_inbox(author) == []
    assert list_review_inbox(helper) == []


@pytest.mark.django_db
def test_non_helper_cannot_approve():
    author = Actor(
        kind="account",
        account=Account.objects.create_user(
            email="noh@ex.com", password="password123"
        ),
    )
    story = publish_story(author, "монолог")
    peer = Actor(kind="anonymous", session=AnonymousSession.objects.create())
    req = create_request(peer, story.id, intent="listen")
    with pytest.raises(DialogueError):
        approve_dialogue_request(author, req.id)
