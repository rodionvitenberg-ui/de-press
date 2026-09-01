"""Signed anon-session cookie (audit Q6): a bare UUID is no longer accepted."""

from __future__ import annotations

import pytest
from django.conf import settings
from django.test import RequestFactory

from apps.identity.cookies import resolve_anon_session_id, sign_anon_session_id
from apps.identity.middleware import _load_anon_session
from apps.identity.models import AnonymousSession


@pytest.mark.django_db
def test_signed_value_resolves_and_differs_from_bare_id():
    session = AnonymousSession.objects.create()
    signed = sign_anon_session_id(str(session.id))

    assert signed != str(session.id)
    assert resolve_anon_session_id(signed) == session.id


@pytest.mark.django_db
def test_bare_uuid_forgery_and_empty_are_rejected():
    session = AnonymousSession.objects.create()

    assert resolve_anon_session_id(str(session.id)) is None
    assert resolve_anon_session_id(f"{session.id}:forged") is None
    assert resolve_anon_session_id("") is None
    assert resolve_anon_session_id(None) is None


@pytest.mark.django_db
def test_middleware_ignores_legacy_cookie_and_accepts_signed():
    session = AnonymousSession.objects.create()

    request = RequestFactory().get("/")
    request.COOKIES[settings.ANON_SESSION_COOKIE_NAME] = str(session.id)
    assert _load_anon_session(request) is None

    request = RequestFactory().get("/")
    request.COOKIES[settings.ANON_SESSION_COOKIE_NAME] = sign_anon_session_id(
        str(session.id)
    )
    assert _load_anon_session(request) == session
