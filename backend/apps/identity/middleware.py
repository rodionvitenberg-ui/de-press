"""Attach AnonymousSession from cookie; set cookie when newly minted."""

from __future__ import annotations

from uuid import UUID

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from apps.identity.models import AnonymousSession


def _load_anon_session(request: HttpRequest) -> AnonymousSession | None:
    raw = request.COOKIES.get(settings.ANON_SESSION_COOKIE_NAME)
    if not raw:
        return None
    try:
        session_id = UUID(raw)
    except (ValueError, TypeError):
        return None
    return AnonymousSession.objects.filter(pk=session_id).first()


class AnonymousSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.anonymous_session = _load_anon_session(request)
        request._anon_session_just_created = False  # type: ignore[attr-defined]

        response = self.get_response(request)

        if getattr(request, "_anon_session_just_created", False):
            session = getattr(request, "anonymous_session", None)
            if session is not None:
                response.set_cookie(
                    settings.ANON_SESSION_COOKIE_NAME,
                    str(session.id),
                    max_age=settings.ANON_SESSION_COOKIE_MAX_AGE,
                    httponly=True,
                    samesite="Lax",
                    secure=not settings.DEBUG,
                )

        return response
