from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from django.test import override_settings

from apps.identity.models import Account
from apps.identity.services import Actor
from apps.notifications.models import Notification, NotificationKind
from apps.notifications.telegram_notify import (
    account_wants_telegram_daily_digest,
    account_wants_telegram_soft_notify,
    format_digest_text,
    format_soft_notify_text,
    maybe_send_telegram_soft_notify,
    mini_app_deep_link,
    run_telegram_daily_digests,
    send_telegram_daily_digest_for_account,
    startapp_for_notification,
    unread_for_telegram_digest,
)


def test_startapp_for_notification_mapping():
    did = str(uuid4())
    sid = str(uuid4())
    assert (
        startapp_for_notification("message", {"dialogue_id": did})
        == f"chat_{did}"
    )
    assert (
        startapp_for_notification("support_cloud", {"story_id": sid})
        == f"story_{sid}"
    )
    assert startapp_for_notification("dialogue_request", {}) == "chat"
    assert startapp_for_notification("cloud_approved", {}) == "notifications"


@override_settings(TELEGRAM_BOT_USERNAME="depress_bot")
def test_mini_app_deep_link():
    assert (
        mini_app_deep_link("inbox")
        == "https://t.me/depress_bot?startapp=inbox"
    )


@override_settings(TELEGRAM_BOT_USERNAME="")
@override_settings(PUBLIC_BASE_URL="http://127.0.0.1:5174")
def test_mini_app_deep_link_web_fallback():
    assert (
        mini_app_deep_link("chat")
        == "http://127.0.0.1:5174/?startapp=chat"
    )


def test_format_soft_notify_text_contains_label():
    text = format_soft_notify_text("message", {"dialogue_id": str(uuid4())})
    assert "de-press:" in text
    assert "сообщени" in text.lower() or "диалог" in text.lower()


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN="1:test")
def test_account_wants_telegram_soft_notify():
    acc = Account.objects.create_user(
        email="tg1@users.de-press.local",
        password=None,
    )
    acc.set_unusable_password()
    acc.telegram_id = 1001
    acc.notify_telegram_opt_in = True
    acc.notify_digest_frequency = "immediate"
    acc.save()
    assert account_wants_telegram_soft_notify(acc) is True

    acc.notify_telegram_opt_in = False
    acc.save(update_fields=["notify_telegram_opt_in"])
    assert account_wants_telegram_soft_notify(acc) is False


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN="1:test", TELEGRAM_BOT_USERNAME="bot")
def test_maybe_send_calls_bot_api():
    acc = Account.objects.create_user(
        email="tg2@users.de-press.local",
        password="unusedpass1",
    )
    acc.telegram_id = 2002
    acc.notify_telegram_opt_in = True
    acc.notify_digest_frequency = "immediate"
    acc.save()

    notif = Notification.objects.create(
        recipient_account=acc,
        kind=NotificationKind.MESSAGE,
        payload={"dialogue_id": str(uuid4())},
    )
    actor = Actor(kind="account", account=acc)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "ok"

    with patch("apps.notifications.telegram_notify.httpx.Client") as client_cls:
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.post.return_value = mock_resp
        client_cls.return_value = client

        ok = maybe_send_telegram_soft_notify(actor, notif)
        assert ok is True
        client.post.assert_called_once()
        args, kwargs = client.post.call_args
        assert "sendMessage" in args[0]
        assert kwargs["json"]["chat_id"] == 2002


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN="1:test")
def test_daily_digest_wants_and_unread_window():
    acc = Account.objects.create_user(
        email="tg3@users.de-press.local",
        password="unusedpass1",
    )
    acc.telegram_id = 3003
    acc.notify_telegram_opt_in = True
    acc.notify_digest_frequency = "daily"
    acc.save()
    assert account_wants_telegram_daily_digest(acc) is True
    assert account_wants_telegram_soft_notify(acc) is False

    n1 = Notification.objects.create(
        recipient_account=acc,
        kind=NotificationKind.MESSAGE,
        payload={},
    )
    rows = unread_for_telegram_digest(acc)
    assert n1 in rows
    text = format_digest_text(rows)
    assert "дайджест" in text.lower()
    assert "de-press:" in text


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN="1:test", TELEGRAM_BOT_USERNAME="bot")
def test_send_daily_digest_updates_last_at():
    acc = Account.objects.create_user(
        email="tg4@users.de-press.local",
        password="unusedpass1",
    )
    acc.telegram_id = 4004
    acc.notify_telegram_opt_in = True
    acc.notify_digest_frequency = "daily"
    acc.save()
    Notification.objects.create(
        recipient_account=acc,
        kind=NotificationKind.DIALOGUE_REQUEST,
        payload={},
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "ok"

    with patch("apps.notifications.telegram_notify.httpx.Client") as client_cls:
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.post.return_value = mock_resp
        client_cls.return_value = client

        status = send_telegram_daily_digest_for_account(acc)
        assert status == "sent"
        acc.refresh_from_db()
        assert acc.telegram_digest_last_at is not None

        # Second run: no notifications newer than last_at → empty
        status2 = send_telegram_daily_digest_for_account(acc)
        assert status2 == "skipped_empty"


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN="1:test")
def test_run_batch_counts():
    stats = run_telegram_daily_digests(limit_accounts=10)
    assert "sent" in stats
    assert "candidates" in stats
