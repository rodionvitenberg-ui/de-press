import pytest
from django.db import IntegrityError

from apps.dialogue.help import (
    HelpError,
    accept_help_request,
    cancel_help_request,
    create_help_request,
    list_help_inbox,
    skip_help_request,
)
from apps.dialogue.models import Dialogue, DialogueSource, HelpRequest, HelpRequestSkip
from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor
from apps.notifications.models import Notification, NotificationKind


@pytest.mark.django_db
def test_help_request_one_pending_per_account():
    acc = Account.objects.create_user(email="u@ex.com", password="password123")
    HelpRequest.objects.create(from_account=acc, note="тихо")
    with pytest.raises(IntegrityError):
        HelpRequest.objects.create(from_account=acc, note="ещё")


@pytest.mark.django_db
def test_dialogue_help_allows_null_story():
    helper = Account.objects.create_user(
        email="h@ex.com", password="password123", is_helper=True
    )
    sess = AnonymousSession.objects.create(pseudonym="гость")
    d = Dialogue.objects.create(
        story=None,
        source=DialogueSource.HELP,
        author_session=sess,
        peer_account=helper,
    )
    assert d.story_id is None
    assert d.source == DialogueSource.HELP


@pytest.mark.django_db
def test_anon_create_helper_accept_creates_dialogue_without_story():
    helper_acc = Account.objects.create_user(
        email="helper@ex.com", password="password123", is_helper=True
    )
    helper = Actor(kind="account", account=helper_acc)
    sess = AnonymousSession.objects.create(pseudonym="гость")
    visitor = Actor(kind="anonymous", session=sess)

    req = create_help_request(visitor, note="мне тяжело")
    assert req.status == "pending"
    assert Notification.objects.filter(
        kind=NotificationKind.HELP_REQUESTED, recipient_account=helper_acc
    ).exists()
    assert list_help_inbox(helper)[0].id == req.id

    dialogue = accept_help_request(helper, req.id)
    assert dialogue.story_id is None
    assert dialogue.source == "help"
    assert dialogue.author_session_id == sess.id
    assert dialogue.peer_account_id == helper_acc.id
    req.refresh_from_db()
    assert req.status == "accepted"
    assert req.dialogue_id == dialogue.id
    assert Notification.objects.filter(
        kind=NotificationKind.HELP_ACCEPTED, recipient_session=sess
    ).exists()
    assert list_help_inbox(helper) == []


@pytest.mark.django_db
def test_second_helper_loses_the_race():
    h1 = Account.objects.create_user(email="h1@ex.com", password="password123", is_helper=True)
    h2 = Account.objects.create_user(email="h2@ex.com", password="password123", is_helper=True)
    sess = AnonymousSession.objects.create()
    req = create_help_request(Actor(kind="anonymous", session=sess))
    accept_help_request(Actor(kind="account", account=h1), req.id)
    with pytest.raises(HelpError):
        accept_help_request(Actor(kind="account", account=h2), req.id)


@pytest.mark.django_db
def test_skip_hides_only_for_that_helper():
    h1 = Account.objects.create_user(email="s1@ex.com", password="password123", is_helper=True)
    h2 = Account.objects.create_user(email="s2@ex.com", password="password123", is_helper=True)
    sess = AnonymousSession.objects.create()
    req = create_help_request(Actor(kind="anonymous", session=sess))
    skip_help_request(Actor(kind="account", account=h1), req.id)
    assert list_help_inbox(Actor(kind="account", account=h1)) == []
    assert list_help_inbox(Actor(kind="account", account=h2))[0].id == req.id
    req.refresh_from_db()
    assert req.status == "pending"


@pytest.mark.django_db
def test_create_is_idempotent_pending():
    sess = AnonymousSession.objects.create()
    visitor = Actor(kind="anonymous", session=sess)
    a = create_help_request(visitor, note="раз")
    b = create_help_request(visitor, note="два")
    assert a.id == b.id
    assert b.note == "раз"  # first note kept


@pytest.mark.django_db
def test_cancel_by_requester():
    helper = Account.objects.create_user(email="c@ex.com", password="password123", is_helper=True)
    sess = AnonymousSession.objects.create()
    visitor = Actor(kind="anonymous", session=sess)
    req = create_help_request(visitor)
    cancel_help_request(visitor, req.id)
    req.refresh_from_db()
    assert req.status == "cancelled"
    assert list_help_inbox(Actor(kind="account", account=helper)) == []


@pytest.mark.django_db
def test_non_helper_cannot_accept():
    acc = Account.objects.create_user(email="n@ex.com", password="password123")
    sess = AnonymousSession.objects.create()
    req = create_help_request(Actor(kind="anonymous", session=sess))
    with pytest.raises(HelpError):
        accept_help_request(Actor(kind="account", account=acc), req.id)


@pytest.mark.django_db
def test_helper_cannot_accept_own_request():
    helper = Account.objects.create_user(email="self@ex.com", password="password123", is_helper=True)
    actor = Actor(kind="account", account=helper)
    req = create_help_request(actor)
    assert list_help_inbox(actor) == []
    with pytest.raises(HelpError):
        accept_help_request(actor, req.id)
