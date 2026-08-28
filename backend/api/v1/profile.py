"""Личный кабинет: настройки soft-notify, контактный email, тест дайджеста."""

from __future__ import annotations

from ninja import Router, Schema
from ninja.errors import HttpError

from apps.identity.services import (
    AuthError,
    get_voice_retention,
    require_actor,
    set_voice_retention,
)
from apps.notifications.softnotify import (
    SoftNotifyError,
    send_soft_notify,
    verify_session_email,
)
from apps.notifications.telegram_notify import (
    send_telegram_daily_digest_for_account,
)

router = Router(tags=["profile"])


class NotifySettingsIn(Schema):
    notify_email_opt_in: bool = False
    notify_digest_frequency: str = "daily"
    contact_email: str = ""  # For anonymous session only
    notify_telegram_opt_in: bool | None = None  # Account + telegram_id only


class NotifySettingsOut(Schema):
    ok: bool
    email: str = ""
    notify_email_opt_in: bool = False
    notify_digest_frequency: str = "off"
    email_verified: bool = False
    has_telegram: bool = False
    notify_telegram_opt_in: bool = False


class DigestTestOut(Schema):
    ok: bool
    sent_to: str
    message: str


def _settings_out(actor) -> NotifySettingsOut:
    if actor.account is not None:
        acc = actor.account
        return NotifySettingsOut(
            ok=True,
            email=acc.email or "",
            notify_email_opt_in=bool(acc.notify_email_opt_in),
            notify_digest_frequency=acc.notify_digest_frequency or "off",
            email_verified=bool(acc.email_verified),
            has_telegram=bool(acc.telegram_id),
            notify_telegram_opt_in=bool(
                getattr(acc, "notify_telegram_opt_in", False)
            ),
        )
    sess = actor.session
    if sess is not None:
        return NotifySettingsOut(
            ok=True,
            email=sess.notify_email or "",
            notify_email_opt_in=bool(sess.notify_email_opt_in),
            notify_digest_frequency=sess.notify_digest_frequency or "off",
            email_verified=bool(sess.contact_email_verified),
            has_telegram=False,
            notify_telegram_opt_in=False,
        )
    return NotifySettingsOut(
        ok=True,
        notify_digest_frequency="off",
    )


class VoiceRetentionOut(Schema):
    voice_retention: str


class VoiceRetentionIn(Schema):
    voice_retention: str


@router.get("/me/voice-retention", response=VoiceRetentionOut)
def get_me_voice_retention(request):
    actor = require_actor(request)
    return VoiceRetentionOut(voice_retention=get_voice_retention(actor))


@router.post("/me/voice-retention", response=VoiceRetentionOut)
def post_me_voice_retention(request, payload: VoiceRetentionIn):
    actor = require_actor(request)
    try:
        value = set_voice_retention(actor, payload.voice_retention)
    except AuthError as exc:
        raise HttpError(400, str(exc)) from exc
    return VoiceRetentionOut(voice_retention=value)


@router.get("/me/notify-settings", response=NotifySettingsOut)
def get_notify_settings(request):
    actor = require_actor(request)
    return _settings_out(actor)


@router.post("/me/notify-settings", response=NotifySettingsOut)
def update_notify_settings(request, payload: NotifySettingsIn):
    actor = require_actor(request)

    freq = (payload.notify_digest_frequency or "off").lower().strip()
    if freq not in ("off", "immediate", "daily"):
        raise HttpError(400, "Invalid notify_digest_frequency")

    try:
        verify_session_email(actor, email=payload.contact_email or None)
    except SoftNotifyError as exc:
        raise HttpError(400, str(exc)) from exc

    if actor.account is not None:
        acc = actor.account
        acc.notify_email_opt_in = bool(payload.notify_email_opt_in)
        acc.notify_digest_frequency = freq
        fields = ["notify_email_opt_in", "notify_digest_frequency"]
        if payload.notify_telegram_opt_in is not None:
            if not acc.telegram_id:
                raise HttpError(
                    400,
                    "Telegram soft-notify requires Mini App login first",
                )
            acc.notify_telegram_opt_in = bool(payload.notify_telegram_opt_in)
            fields.append("notify_telegram_opt_in")
        acc.save(update_fields=fields)
    elif actor.session is not None:
        if payload.notify_telegram_opt_in:
            raise HttpError(400, "Telegram soft-notify only for linked accounts")
        sess = actor.session
        sess.notify_email_opt_in = bool(payload.notify_email_opt_in)
        sess.notify_digest_frequency = freq
        sess.save(
            update_fields=["notify_email_opt_in", "notify_digest_frequency"]
        )
    else:
        raise HttpError(400, "Нет идентичности")

    return _settings_out(actor)


@router.post("/me/notify-settings/test", response=DigestTestOut)
def send_test_digest(request):
    """Отправить тестовый дайджест на контактный email (для проверки SMTP)."""
    actor = require_actor(request)
    try:
        digest = send_soft_notify(actor, notifications=[])
    except SoftNotifyError as exc:
        raise HttpError(400, str(exc)) from exc
    if digest is None:
        raise HttpError(400, "Нет email или soft-notify отключено")
    return DigestTestOut(
        ok=True,
        sent_to=digest.to_email,
        message=(
            "Дайджест отправлен на почту."
            if digest.status == "sent"
            else f"Не удалось отправить: {digest.failed_reason or 'ошибка SMTP'}"
        ),
    )


@router.post("/me/notify-settings/test-telegram", response=DigestTestOut)
def send_test_telegram_digest(request):
    """Force-run Telegram digest logic for the current account (dev / check bot)."""
    actor = require_actor(request)
    if actor.account is None:
        raise HttpError(400, "Нужен аккаунт (войди через Mini App)")
    acc = actor.account
    if not acc.telegram_id:
        raise HttpError(400, "Аккаунт не связан с Telegram")
    if not acc.notify_telegram_opt_in:
        raise HttpError(400, "Включи тихие напоминания в Telegram")
    # Temporarily treat as daily for the test path if frequency is immediate —
    # still only sends when there is unread (or skipped_empty).
    status = send_telegram_daily_digest_for_account(acc)
    # If user is on immediate, daily check returns skipped_freq — force body once.
    if status == "skipped_freq":
        from apps.notifications.telegram_notify import (
            format_digest_text,
            send_bot_message,
            unread_for_telegram_digest,
        )

        rows = unread_for_telegram_digest(acc)
        if not rows:
            status = "skipped_empty"
        else:
            ok = send_bot_message(
                chat_id=int(acc.telegram_id),
                text=format_digest_text(rows),
            )
            status = "sent" if ok else "failed"

    messages = {
        "sent": "Дайджест отправлен в Telegram.",
        "skipped_empty": "Нет новых непрочитанных — сообщение не слали.",
        "skipped_config": "Бот не настроен (TELEGRAM_BOT_TOKEN).",
        "skipped_freq": "Частота не daily.",
        "failed": "Bot API не принял сообщение.",
    }
    return DigestTestOut(
        ok=status in ("sent", "skipped_empty"),
        sent_to=f"tg:{acc.telegram_id}",
        message=messages.get(status, status),
    )