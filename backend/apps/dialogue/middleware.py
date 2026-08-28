"""ASGI middleware: attach Actor from session cookie + anonymous cookie."""

from __future__ import annotations

from urllib.parse import parse_qs
from uuid import UUID

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor


@database_sync_to_async
def _load_account(user_id) -> Account | None:
    if not user_id:
        return None
    return Account.objects.filter(pk=user_id).first()


@database_sync_to_async
def _load_anon(session_id: str | None) -> AnonymousSession | None:
    if not session_id:
        return None
    try:
        uid = UUID(session_id)
    except (ValueError, TypeError):
        return None
    return AnonymousSession.objects.filter(pk=uid).first()


class ActorAuthMiddleware(BaseMiddleware):
    """
    After AuthMiddlewareStack: scope['user'] may be Account.
    Also reads depress_anon cookie (or ?anon= query for tools).
    Sets scope['actor'] = Actor.
    """

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        user = scope.get("user", AnonymousUser())
        account = None
        if getattr(user, "is_authenticated", False):
            account = user if isinstance(user, Account) else await _load_account(
                getattr(user, "pk", None)
            )

        cookies = scope.get("cookies") or {}
        anon_raw = cookies.get(settings.ANON_SESSION_COOKIE_NAME)
        if not anon_raw:
            qs = parse_qs(scope.get("query_string", b"").decode())
            anon_raw = (qs.get("anon") or [None])[0]

        session = await _load_anon(anon_raw)

        if account is not None:
            scope["actor"] = Actor(kind="account", account=account, session=session)
        elif session is not None:
            scope["actor"] = Actor(kind="anonymous", session=session)
        else:
            scope["actor"] = Actor(kind="anonymous", session=None)

        return await super().__call__(scope, receive, send)


def ActorAuthMiddlewareStack(inner):
    from channels.auth import AuthMiddlewareStack

    return AuthMiddlewareStack(ActorAuthMiddleware(inner))
