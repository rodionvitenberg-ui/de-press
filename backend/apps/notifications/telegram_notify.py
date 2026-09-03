"""Soft-notify via Telegram Bot API (Mini App host).

Opt-in only. Immediate pings + daily digests with startapp deep-links.
Does not use Telegram chats as dialogue transport — only a nudge + link back.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any, Literal
from uuid import UUID

import httpx
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.identity.models import Account
from apps.identity.services import Actor
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)

KIND_LABELS = {
    "dialogue_request": "Dialogue request on your story",
    "support_cloud": "New support cloud",
    "cloud_approved": "Support cloud approved",
    "dialogue_opened": "Dialogue opened",
    "outreach_intro": "A hearer of your story wrote to you",
    "message": "New message in a dialogue",
    "dialogue_deleted": "Your dialogue partner deleted the dialogue",
}

DigestStatus = Literal[
    "sent",
    "skipped_empty",
    "skipped_config",
    "skipped_freq",
    "failed",
]


def _bot_token() -> str:
    return (getattr(settings, "TELEGRAM_BOT_TOKEN", None) or "").strip()


def _bot_username() -> str:
    return (getattr(settings, "TELEGRAM_BOT_USERNAME", None) or "").strip().lstrip(
        "@"
    )


def startapp_for_notification(kind: str, payload: dict[str, Any] | None) -> str:
    """Map notification → startapp param (max 64 chars, Telegram alphabet)."""
    data = dict(payload or {})

    def _uuid(key: str) -> str | None:
        raw = data.get(key)
        if not raw:
            return None
        try:
            return str(UUID(str(raw)))
        except (ValueError, TypeError):
            return None

    dialogue_id = _uuid("dialogue_id")
    story_id = _uuid("story_id")

    if kind in (
        "message",
        "dialogue_opened",
        "outreach_intro",
        "dialogue_deleted",
    ) and dialogue_id:
        return f"chat_{dialogue_id}"
    if kind == "dialogue_request":
        if dialogue_id:
            return f"chat_{dialogue_id}"
        if story_id:
            return f"story_{story_id}"
        return "chat"
    if kind in ("support_cloud", "cloud_approved"):
        if story_id:
            return f"story_{story_id}"
        return "notifications"
    return "notifications"


def mini_app_deep_link(startapp: str) -> str:
    """t.me deep link when bot username is configured; else web PUBLIC_BASE_URL."""
    param = (startapp or "notifications").strip()[:64]
    username = _bot_username()
    if username:
        return f"https://t.me/{username}?startapp={param}"
    base = (getattr(settings, "PUBLIC_BASE_URL", None) or "").rstrip("/")
    if base:
        return f"{base}/?startapp={param}"
    return ""


def format_soft_notify_text(kind: str, payload: dict[str, Any] | None) -> str:
    label = KIND_LABELS.get(kind, "New notification in de-press")
    startapp = startapp_for_notification(kind, payload)
    link = mini_app_deep_link(startapp)
    lines = [f"de-press: {label}"]
    if link:
        lines.append("")
        lines.append(f"Open: {link}")
    lines.append("")
    lines.append("Quiet reminder. Turn off: menu → notifications in Telegram.")
    return "\n".join(lines)


def send_bot_message(*, chat_id: int, text: str) -> bool:
    """POST sendMessage. Returns True on HTTP ok. No-op if token missing."""
    token = _bot_token()
    if not token or not chat_id or not text:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        with httpx.Client(timeout=8.0) as client:
            res = client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text[:4000],
                    "disable_web_page_preview": True,
                },
            )
        if res.status_code >= 400:
            logger.warning(
                "telegram sendMessage failed: %s %s",
                res.status_code,
                res.text[:200],
            )
            return False
        return True
    except Exception:
        logger.exception("telegram sendMessage error")
        return False


def _account_base_tg_ok(account: Account) -> bool:
    if not account or not account.telegram_id:
        return False
    if not bool(getattr(account, "notify_telegram_opt_in", False)):
        return False
    if not _bot_token():
        return False
    return True


def account_wants_telegram_soft_notify(account: Account) -> bool:
    """Immediate per-event Bot pings."""
    if not _account_base_tg_ok(account):
        return False
    freq = (account.notify_digest_frequency or "off").lower()
    return freq == "immediate"


def account_wants_telegram_daily_digest(account: Account) -> bool:
    """Daily batch digest (not per-event)."""
    if not _account_base_tg_ok(account):
        return False
    freq = (account.notify_digest_frequency or "off").lower()
    return freq == "daily"


def maybe_send_telegram_soft_notify(
    recipient: Actor,
    notification: Notification,
) -> bool:
    """Send TG soft-notify if recipient is opt-in TG account. Safe no-op otherwise."""
    account = recipient.account
    if account is None or not account_wants_telegram_soft_notify(account):
        return False
    text = format_soft_notify_text(notification.kind, notification.payload)
    return send_bot_message(chat_id=int(account.telegram_id), text=text)


def schedule_telegram_soft_notify(
    recipient: Actor,
    notification: Notification,
) -> None:
    """Defer send until after DB commit (same pattern as WS broadcast)."""

    notif_id = notification.pk
    account_id = recipient.account_id

    def _send() -> None:
        if account_id is None:
            return
        try:
            account = Account.objects.get(pk=account_id)
            notif = Notification.objects.get(pk=notif_id)
        except (Account.DoesNotExist, Notification.DoesNotExist):
            return
        actor = Actor(kind="account", account=account)
        maybe_send_telegram_soft_notify(actor, notif)

    transaction.on_commit(_send)


def unread_for_telegram_digest(
    account: Account,
    *,
    limit: int = 20,
) -> list[Notification]:
    """Unread notifications since last successful daily digest (or all if never)."""
    limit = max(1, min(int(limit or 20), 50))
    q = Q(recipient_account=account, is_read=False)
    last = getattr(account, "telegram_digest_last_at", None)
    if last is not None:
        q &= Q(created_at__gt=last)
    return list(
        Notification.objects.filter(q).order_by("-created_at", "-id")[:limit]
    )


def format_digest_text(notifications: list[Notification]) -> str:
    """One soft digest message: counts by kind + open inbox link."""
    counts = Counter(n.kind for n in notifications)
    lines = [f"de-press: quiet digest ({len(notifications)})"]
    for kind, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        label = KIND_LABELS.get(kind, kind)
        lines.append(f"• {count}× {label}")
    link = mini_app_deep_link("notifications")
    if link:
        lines.append("")
        lines.append(f"Open: {link}")
    lines.append("")
    lines.append("Quiet. Turn off: menu → notifications in Telegram.")
    return "\n".join(lines)


def send_telegram_daily_digest_for_account(account: Account) -> DigestStatus:
    """Send one daily digest if eligible and there is new unread. Updates last_at."""
    if not account_wants_telegram_daily_digest(account):
        if not _account_base_tg_ok(account):
            return "skipped_config"
        return "skipped_freq"

    rows = unread_for_telegram_digest(account)
    if not rows:
        return "skipped_empty"

    text = format_digest_text(rows)
    ok = send_bot_message(chat_id=int(account.telegram_id), text=text)
    if not ok:
        return "failed"

    account.telegram_digest_last_at = timezone.now()
    account.save(update_fields=["telegram_digest_last_at"])
    return "sent"


def run_telegram_daily_digests(*, limit_accounts: int = 500) -> dict[str, int]:
    """Batch job: daily digests for all eligible accounts.

    Returns counters: sent, skipped_empty, skipped_config, skipped_freq, failed.
    """
    stats: dict[str, int] = {
        "sent": 0,
        "skipped_empty": 0,
        "skipped_config": 0,
        "skipped_freq": 0,
        "failed": 0,
        "candidates": 0,
    }
    if not _bot_token():
        return stats

    qs = (
        Account.objects.filter(
            is_active=True,
            notify_telegram_opt_in=True,
            notify_digest_frequency="daily",
            telegram_id__isnull=False,
        )
        .order_by("id")[: max(1, min(int(limit_accounts or 500), 5000))]
    )
    for account in qs:
        stats["candidates"] += 1
        status = send_telegram_daily_digest_for_account(account)
        stats[status] = stats.get(status, 0) + 1
    return stats
