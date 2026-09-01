"""Signed anon-session cookie values (audit Q6).

A bare UUID in the cookie makes "know the id" equivalent to "own the
identity" — ids leak via server logs, DB dumps and support screenshots.
The HMAC signature (SECRET_KEY + salt) exists only inside the cookie, so a
leaked id alone is no longer a bearer token; forged values are rejected
before any DB lookup.
"""

from __future__ import annotations

from uuid import UUID

from django.conf import settings
from django.core import signing

_SALT = "depress.anon-session"


def sign_anon_session_id(session_id: str) -> str:
    """Cookie value for an AnonymousSession id (timestamped signature)."""
    return signing.dumps(session_id, salt=_SALT)


def resolve_anon_session_id(raw: str | None) -> UUID | None:
    """Verify the signed value and return the session UUID, else None."""
    if not raw:
        return None
    try:
        value = signing.loads(
            raw,
            salt=_SALT,
            max_age=settings.ANON_SESSION_COOKIE_MAX_AGE,
        )
    except signing.BadSignature:
        return None
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None
