from __future__ import annotations

from ninja import Router, Schema
from ninja.errors import HttpError

from api.deps import get_optional_actor
from apps.identity.services import (
    AuthError,
    DutyError,
    login_account,
    logout_account,
    register,
    resolve_actor,
    set_helper_duty,
)
from apps.identity.telegram import login_or_register_telegram
from apps.notifications.softnotify import SoftNotifyError, open_inbox

router = Router(tags=["identity"])


class RegisterIn(Schema):
    email: str
    password: str
    pseudonym: str = ""


class LoginIn(Schema):
    email: str
    password: str


class MeOut(Schema):
    kind: str
    email: str | None = None
    account_id: str | None = None
    session_id: str | None = None
    pseudonym: str
    is_authenticated: bool
    is_helper: bool = False
    is_staff: bool = False
    is_on_duty: bool = False
    helper_org: str = ""
    helper_badge: str = ""


def _me_from_account(account) -> MeOut:
    return MeOut(
        kind="account",
        email=account.email,
        account_id=str(account.id),
        session_id=None,
        pseudonym=account.display_pseudonym,
        is_authenticated=True,
        is_helper=bool(account.is_helper),
        is_staff=bool(account.is_staff or account.is_superuser),
        is_on_duty=bool(account.is_helper and account.is_on_duty),
        helper_org=account.helper_org or "",
        helper_badge=account.helper_badge_label if account.is_helper else "",
    )


@router.post("/auth/register", response=MeOut)
def auth_register(request, payload: RegisterIn):
    try:
        account = register(
            email=payload.email,
            password=payload.password,
            pseudonym=payload.pseudonym,
            request=request,
        )
    except AuthError as exc:
        raise HttpError(400, str(exc)) from exc
    return _me_from_account(account)


@router.post("/auth/login", response=MeOut)
def auth_login(request, payload: LoginIn):
    try:
        account = login_account(
            email=payload.email,
            password=payload.password,
            request=request,
        )
    except AuthError as exc:
        raise HttpError(400, str(exc)) from exc
    return _me_from_account(account)


@router.post("/auth/logout")
def auth_logout(request):
    logout_account(request)
    return {"ok": True}


class TelegramAuthIn(Schema):
    """Raw query string from Telegram.WebApp.initData (not initDataUnsafe)."""

    init_data: str


@router.post("/auth/telegram", response=MeOut)
def auth_telegram(request, payload: TelegramAuthIn):
    """Seamless login for Telegram Mini App host.

    Validates HMAC of initData with TELEGRAM_BOT_TOKEN, then creates/links
    an Account by telegram_id and opens a Django session. Dialogues stay
    on de-press backend — Telegram is only identity/host here.
    """
    try:
        account = login_or_register_telegram(
            init_data=payload.init_data,
            request=request,
        )
    except AuthError as exc:
        raise HttpError(400, str(exc)) from exc
    return _me_from_account(account)


class InboxIn(Schema):
    token: str


class InboxOut(Schema):
    ok: bool
    kind: str
    opened: int = 0


@router.post("/auth/inbox", response=InboxOut)
def auth_inbox(request, payload: InboxIn):
    """Open the private inbox via a magic token from a soft-notify email.

    Logs the account in (or binds the anonymous session) and marks the
    digest's notifications as read. No password required.
    """
    try:
        digest, actor = open_inbox(request, payload.token)
    except SoftNotifyError as exc:
        raise HttpError(400, str(exc)) from exc
    return InboxOut(
        ok=True,
        kind=actor.kind,
        opened=len(digest.payload.get("notification_ids") or []),
    )


@router.get("/me", response=MeOut)
def me(request):
    actor = resolve_actor(request)
    if actor.account is not None:
        return _me_from_account(actor.account)
    return MeOut(
        kind=actor.kind,
        email=None,
        account_id=None,
        session_id=str(actor.session.id) if actor.session else None,
        pseudonym=actor.display_pseudonym,
        is_authenticated=False,
        is_helper=False,
        is_staff=False,
        is_on_duty=False,
        helper_org="",
        helper_badge="",
    )


class HelperDutyIn(Schema):
    on: bool


@router.post("/me/helper-duty", response=MeOut)
def helper_duty(request, payload: HelperDutyIn):
    actor = resolve_actor(request)
    try:
        account = set_helper_duty(actor, payload.on)
    except DutyError as exc:
        raise HttpError(403, str(exc)) from exc
    return _me_from_account(account)
