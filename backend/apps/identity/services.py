"""Deep identity module: small interface for actors and auth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.http import HttpRequest

from apps.fund import services as fund_services
from apps.identity.models import Account, AnonymousSession, VoiceRetention


@dataclass(frozen=True, slots=True)
class Actor:
    """Resolved subject of an action."""

    kind: Literal["account", "anonymous"]
    account: Account | None = None
    session: AnonymousSession | None = None

    @property
    def is_authenticated_account(self) -> bool:
        return self.kind == "account" and self.account is not None

    @property
    def display_pseudonym(self) -> str:
        if self.account is not None:
            return self.account.display_pseudonym
        if self.session is not None:
            return self.session.display_pseudonym
        return "guest"

    @property
    def account_id(self) -> UUID | None:
        return self.account.id if self.account else None

    @property
    def session_id(self) -> UUID | None:
        return self.session.id if self.session else None


class IdentityError(Exception):
    """Base identity error."""


class AuthError(IdentityError):
    """Login/register failure."""


class DutyError(IdentityError):
    """Helper duty toggle failure."""


def resolve_actor(request: HttpRequest) -> Actor:
    """Resolve Account (if logged in) or AnonymousSession from the request."""
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return Actor(kind="account", account=user)  # type: ignore[arg-type]

    session = getattr(request, "anonymous_session", None)
    if session is not None:
        return Actor(kind="anonymous", session=session)

    return Actor(kind="anonymous", session=None)


def ensure_anonymous_session(request: HttpRequest) -> AnonymousSession:
    """Mint or return the AnonymousSession attached to the request."""
    existing = getattr(request, "anonymous_session", None)
    if existing is not None:
        return existing

    session = AnonymousSession.objects.create()
    request.anonymous_session = session
    request._anon_session_just_created = True  # type: ignore[attr-defined]
    return session


def get_voice_retention(actor: Actor) -> str:
    if actor.account is not None:
        return actor.account.voice_retention or VoiceRetention.DELETE_ON_CLOSE
    if actor.session is not None:
        return actor.session.voice_retention or VoiceRetention.DELETE_ON_CLOSE
    return VoiceRetention.DELETE_ON_CLOSE


def set_voice_retention(actor: Actor, value: str) -> str:
    if value not in VoiceRetention.values:
        raise AuthError("Invalid voice_retention")
    if actor.account is not None:
        actor.account.voice_retention = value
        actor.account.save(update_fields=["voice_retention"])
        return value
    if actor.session is not None:
        actor.session.voice_retention = value
        actor.session.save(update_fields=["voice_retention"])
        return value
    raise AuthError("No identity")


def require_actor(request: HttpRequest) -> Actor:
    """Return an Actor that can perform write actions (mints anon session if needed)."""
    actor = resolve_actor(request)
    if actor.account is not None:
        return actor
    if actor.session is not None:
        return actor
    session = ensure_anonymous_session(request)
    return Actor(kind="anonymous", session=session)


@transaction.atomic
def register(
    *,
    email: str,
    password: str,
    pseudonym: str = "",
    request: HttpRequest | None = None,
) -> Account:
    email_norm = email.strip().lower()
    if Account.objects.filter(email__iexact=email_norm).exists():
        raise AuthError("Account with this email already exists")
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters")

    account = Account.objects.create_user(
        email=email_norm,
        password=password,
        default_pseudonym=pseudonym.strip()[:64],
    )
    if request is not None:
        login(request, account)
    return account


def login_account(
    *,
    email: str,
    password: str,
    request: HttpRequest,
) -> Account:
    account = authenticate(
        request,
        username=email.strip().lower(),
        password=password,
    )
    if account is None:
        raise AuthError("Invalid email or password")
    login(request, account)
    return account  # type: ignore[return-value]


def logout_account(request: HttpRequest) -> None:
    logout(request)


def set_helper_duty(actor: Actor, on: bool) -> Account:
    """Toggle Helper shift. Off-duty helpers do not get help/review inbox."""
    if actor.account is None:
        raise DutyError("Need an account")
    if not actor.account.is_helper:
        raise DutyError("Only a Helper can go on duty")
    account = actor.account
    account.is_on_duty = bool(on)
    account.save(update_fields=["is_on_duty"])
    fund_services.on_duty_changed(account)
    return account
