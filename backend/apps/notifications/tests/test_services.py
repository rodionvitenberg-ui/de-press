"""Unit tests for notification services."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.identity.cookies import resolve_anon_session_id
from apps.identity.models import AnonymousSession
from apps.identity.services import Actor
from apps.notifications.models import EmailDigest, Notification
from apps.notifications.softnotify import open_inbox
from apps.notifications.services import (
    NotificationError,
    list_notifications,
    mark_all_read,
    mark_read,
    notify,
    unread_count,
)

Account = get_user_model()


@pytest.mark.django_db(transaction=True)
def test_notify_creates_and_read_state(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    account = Account.objects.create_user(email="n@ex.com", password="password123")
    actor = Actor(kind="account", account=account)

    notif = notify(
        actor,
        "dialogue_request",
        {"story_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert notif.is_read is False
    assert unread_count(actor) == 1

    rows = list_notifications(actor, limit=10)
    assert len(rows) == 1
    assert rows[0].kind == "dialogue_request"

    marked = mark_read(actor, notif.id)
    assert marked.is_read is True
    assert unread_count(actor) == 0


@pytest.mark.django_db
def test_message_kind_is_hidden_from_inbox():
    account = Account.objects.create_user(
        email="msg-hide@ex.com", password="password123"
    )
    actor = Actor(kind="account", account=account)
    notify(actor, "message", {"dialogue_id": "abc"})
    notify(actor, "dialogue_request", {"story_id": "s"})
    kinds = [n.kind for n in list_notifications(actor)]
    assert "message" not in kinds
    assert "dialogue_request" in kinds
    assert unread_count(actor) == 1


@pytest.mark.django_db
def test_support_cloud_kind_is_hidden_from_inbox():
    account = Account.objects.create_user(
        email="cloud-hide@ex.com", password="password123"
    )
    actor = Actor(kind="account", account=account)
    notify(actor, "support_cloud", {"story_id": "s", "post_id": "p"})
    notify(actor, "cloud_approved", {"story_id": "s"})
    notify(actor, "silent_empathy", {"story_id": "s"})
    notify(actor, "dialogue_request", {"story_id": "s"})
    kinds = [n.kind for n in list_notifications(actor)]
    assert "support_cloud" not in kinds
    assert "cloud_approved" not in kinds
    assert "silent_empathy" not in kinds
    assert "dialogue_request" in kinds
    assert unread_count(actor) == 1


@pytest.mark.django_db(transaction=True)
def test_mark_read_requires_recipient(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    owner = Account.objects.create_user(email="owner@ex.com", password="password123")
    other = Account.objects.create_user(email="other@ex.com", password="password123")
    owner_actor = Actor(kind="account", account=owner)
    other_actor = Actor(kind="account", account=other)

    notif = notify(owner_actor, "support_cloud", {"story_id": "x"})

    with pytest.raises(NotificationError):
        mark_read(other_actor, notif.id)


@pytest.mark.django_db(transaction=True)
def test_notify_anonymous_session(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    sess = AnonymousSession.objects.create()
    actor = Actor(kind="anonymous", session=sess)

    notify(actor, "dialogue_opened", {"dialogue_id": "abc"})

    assert Notification.objects.filter(recipient_session=sess).count() == 1
    assert unread_count(actor) == 1
    assert mark_all_read(actor) == 1
    assert unread_count(actor) == 0


@pytest.mark.django_db(transaction=True)
def test_open_inbox_account_marks_read(settings):
    from django.test import Client

    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    account = Account.objects.create_user(email="owner@ex.com", password="password123")
    actor = Actor(kind="account", account=account)
    notif = notify(actor, "support_cloud", {"story_id": "x"})
    digest = EmailDigest.objects.create(
        recipient_account=account,
        to_email=account.email,
        token="tok-account",
        status="sent",
        payload={"notification_ids": [str(notif.id)]},
    )

    client = Client()
    response = client.post(
        "/api/v1/auth/inbox",
        data={"token": digest.token},
        content_type="application/json",
    )

    assert response.status_code == 200
    notif.refresh_from_db()
    assert notif.is_read is True


@pytest.mark.django_db(transaction=True)
def test_open_inbox_anonymous_binds_session(settings):
    from django.test import Client

    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    sess = AnonymousSession.objects.create()
    actor = Actor(kind="anonymous", session=sess)
    notif = notify(actor, "dialogue_opened", {"dialogue_id": "abc"})
    digest = EmailDigest.objects.create(
        recipient_session=sess,
        to_email="anon@example.com",
        token="tok-anon",
        status="sent",
        payload={"notification_ids": [str(notif.id)]},
    )

    client = Client()
    response = client.post(
        "/api/v1/auth/inbox",
        data={"token": digest.token},
        content_type="application/json",
    )

    assert response.status_code == 200
    notif.refresh_from_db()
    assert notif.is_read is True
    cookie = response.cookies.get(settings.ANON_SESSION_COOKIE_NAME)
    assert cookie is not None
    assert resolve_anon_session_id(cookie.value) == sess.id


@pytest.mark.django_db(transaction=True)
def test_open_inbox_invalid_token(settings):
    from django.test import Client

    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    client = Client()
    response = client.post(
        "/api/v1/auth/inbox",
        data={"token": "nope"},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_open_inbox_expired_token(settings):
    from datetime import timedelta

    from django.test import Client
    from django.utils import timezone

    from apps.notifications.softnotify import MAGIC_LINK_TTL_DAYS

    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    account = Account.objects.create_user(
        email="stale@ex.com", password="password123"
    )
    actor = Actor(kind="account", account=account)
    notif = notify(actor, "support_cloud", {"story_id": "x"})
    digest = EmailDigest.objects.create(
        recipient_account=account,
        to_email=account.email,
        token="tok-stale",
        status="sent",
        payload={"notification_ids": [str(notif.id)]},
    )
    # .update() bypasses auto_now_add and backdates the digest.
    EmailDigest.objects.filter(pk=digest.pk).update(
        created_at=timezone.now() - timedelta(days=MAGIC_LINK_TTL_DAYS + 1)
    )

    client = Client()
    response = client.post(
        "/api/v1/auth/inbox",
        data={"token": digest.token},
        content_type="application/json",
    )

    assert response.status_code == 400
    notif.refresh_from_db()
    assert notif.is_read is False
