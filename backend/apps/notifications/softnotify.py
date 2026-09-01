"""Soft-notify (email/web digests) for private nudge events.

Письмо-дайджест собирает непрочитанные Notification получателя
(Account или AnonymousSession) и отправляет одно письмо со ссылкой-токеном
на веб-инбокс (без пароля). В dev используется console.EmailBackend.
"""

from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Any
from uuid import UUID

from django.conf import settings
from django.contrib.auth import login as django_login
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.identity.services import Actor
from apps.notifications.models import EmailDigest, EmailDigestStatus, Notification


class SoftNotifyError(Exception):
    pass


# A magic-link token is a login credential: open_inbox() logs accounts in
# with it, so a leaked link must not stay valid forever.
MAGIC_LINK_TTL_DAYS = 14


def _recipient_contact(actor: Actor) -> str:
    """Best email address for soft-notify ('' if none)."""
    if actor.account is not None:
        return (actor.account.email or "").strip()
    if actor.session is not None:
        return (actor.session.notify_email or "").strip()
    return ""


def _recipient_opt_in(actor: Actor) -> bool:
    if actor.account is not None:
        return bool(actor.account.notify_email_opt_in)
    if actor.session is not None:
        return bool(actor.session.notify_email_opt_in)
    return False


def _recipient_frequency(actor: Actor) -> str:
    if actor.account is not None:
        return (actor.account.notify_digest_frequency or "daily").lower()
    if actor.session is not None:
        return (actor.session.notify_digest_frequency or "daily").lower()
    return "off"


def _build_digest_body(notifications: list[Notification]) -> str:
    """Простые текстовые строки для дайджеста (без HTML в MVP)."""
    lines: list[str] = []
    kind_labels = {
        "dialogue_request": "Запрос диалога по твоей истории",
        "support_cloud": "Новое облачко поддержки",
        "cloud_approved": "Облачко поддержки одобрено",
        "dialogue_opened": "Диалог открыт",
        "outreach_intro": "Написано услышавшим твою историю",
        "message": "Новое сообщение в диалоге",
        "dialogue_deleted": "Собеседник удалил диалог",
    }
    for n in notifications:
        label = kind_labels.get(n.kind, n.kind)
        lines.append(f"• {label}")
    return "\n".join(lines)


def _create_digest(actor: Actor, *, notifications: list[Notification]) -> EmailDigest:
    to_email = _recipient_contact(actor)
    if not to_email:
        raise SoftNotifyError("Нет email для soft-notify")
    if not _recipient_opt_in(actor):
        raise SoftNotifyError("Soft-notify отключено получателем")

    kinds = sorted({n.kind for n in notifications if n.kind})
    digest = EmailDigest.objects.create(
        recipient_account=actor.account,
        recipient_session=actor.session if actor.account is None else None,
        to_email=to_email,
        token=secrets.token_urlsafe(32),
        subject=f"de-press: {len(notifications)} новое",
        body_text=_build_digest_body(notifications),
        payload={
            "unread": len(notifications),
            "kinds": kinds,
            "notification_ids": [str(n.id) for n in notifications],
        },
        status=EmailDigestStatus.PENDING,
    )
    return digest


def _send_digest(digest: EmailDigest) -> EmailDigest:
    magic_url = f"{settings.PUBLIC_BASE_URL}/inbox?token={digest.token}"
    text = (
        f"{digest.body_text}\n\n"
        f"Открыть приватный инбокс: {magic_url}\n\n"
        "Если это не вы — просто проигнорируйте письмо."
    )
    try:
        send_mail(
            subject=digest.subject,
            message=text,
            from_email=None,
            recipient_list=[digest.to_email],
            fail_silently=False,
        )
    except Exception as exc:  # SMTP unavailable → не роняем транзакцию
        digest.status = EmailDigestStatus.FAILED
        digest.failed_reason = str(exc)[:2000]
        digest.save(update_fields=["status", "failed_reason"])
        return digest

    digest.status = EmailDigestStatus.SENT
    digest.sent_at = timezone.now()
    digest.save(update_fields=["status", "sent_at"])
    return digest


@transaction.atomic
def send_soft_notify(
    actor: Actor,
    *,
    notifications: list[Notification] | None = None,
) -> EmailDigest | None:
    """Создать и отправить дайджест для получателя (или None, если нельзя).

    - Требует email (account.email или anon.contact_email) и opt-in.
    - Дайджест отправляется только от имени текущего получателя.
    """
    if not _recipient_opt_in(actor):
        return None
    to_email = _recipient_contact(actor)
    if not to_email:
        return None

    # Явно переданный список (даже пустой) — тестовый режим: использовать как есть.
    # None — обычный режим: собрать непрочитанные уведомления получателя.
    if notifications is None:
        q = Notification.objects.filter(is_read=False)
        if actor.account is not None:
            q = q.filter(recipient_account=actor.account)
        elif actor.session is not None:
            q = q.filter(recipient_session=actor.session)
        else:
            return None
        rows = list(q.order_by("-created_at")[:20])
        if not rows:
            return None
    else:
        rows = list(notifications)

    digest = _create_digest(actor, notifications=rows)
    return _send_digest(digest)


def resolve_digest(token: str) -> EmailDigest:
    """Find digest by magic token; raise SoftNotifyError if it is expired."""
    try:
        digest = EmailDigest.objects.get(token=(token or "").strip())
    except EmailDigest.DoesNotExist as exc:
        raise SoftNotifyError("Неверная ссылка") from exc
    if timezone.now() - digest.created_at > timedelta(days=MAGIC_LINK_TTL_DAYS):
        raise SoftNotifyError("Ссылка устарела")
    return digest


def open_inbox(request, token: str) -> tuple[EmailDigest, Actor]:
    """Resolve a magic token into the recipient Actor and attach it to the request.

    Returns (digest, actor). Marks the digest's notification_ids as read.
    For accounts: logs the account in. For anonymous sessions: binds the
    recipient session as the request's anonymous session and mints/sets the
    anon cookie via the AnonymousSessionMiddleware.
    """
    digest = resolve_digest(token)

    if digest.recipient_account_id is not None:
        account = digest.recipient_account
        django_login(request, account)
        actor = Actor(kind="account", account=account)
    elif digest.recipient_session_id is not None:
        request.anonymous_session = digest.recipient_session
        request._anon_session_just_created = True  # type: ignore[attr-defined]
        actor = Actor(kind="anonymous", session=digest.recipient_session)
    else:
        raise SoftNotifyError("Дайджест без получателя")

    ids = list(digest.payload.get("notification_ids") or [])
    if ids:
        Notification.objects.filter(pk__in=ids, is_read=False).update(is_read=True)

    return digest, actor


def verify_session_email(actor: Actor, email: str | None = None) -> None:
    """Подтвердить/обновить contact_email у анонимной сессии."""
    if actor.account is not None:
        # Для аккаунтов email уже подтверждён регистрацией.
        acc = actor.account
        if email and (email.strip().lower() != acc.email):
            raise SoftNotifyError("Нельзя менять email аккаунта через этот endpoint")
        return
    session = actor.session
    if session is None:
        raise SoftNotifyError("Нет анонимной сессии")
    if email:
        session.contact_email = email.strip().lower()
        session.contact_email_verified = False
    else:
        if not session.contact_email:
            raise SoftNotifyError("Укажи email")
    session.save(update_fields=["contact_email", "contact_email_verified"])