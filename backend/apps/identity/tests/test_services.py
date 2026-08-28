from __future__ import annotations

import pytest
from django.test import RequestFactory

from apps.identity.services import AuthError, register, resolve_actor


@pytest.mark.django_db
def test_register_and_resolve():
    rf = RequestFactory()
    request = rf.post("/api/v1/auth/register")
    # Session + auth attrs required so login() attaches request.user
    from django.contrib.auth.models import AnonymousUser
    from django.contrib.sessions.middleware import SessionMiddleware

    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    request.anonymous_session = None

    account = register(
        email="new@example.com",
        password="password123",
        pseudonym="тихий",
        request=request,
    )
    assert account.email == "new@example.com"
    actor = resolve_actor(request)
    assert actor.is_authenticated_account
    assert actor.display_pseudonym == "тихий"


@pytest.mark.django_db
def test_register_duplicate():
    register(email="dup@example.com", password="password123")
    with pytest.raises(AuthError):
        register(email="dup@example.com", password="password123")


@pytest.mark.django_db
def test_voice_retention_default_delete_on_close():
    from apps.identity.models import Account, AnonymousSession, VoiceRetention

    acc = Account.objects.create_user(email="vr@ex.com", password="password123")
    sess = AnonymousSession.objects.create()
    assert acc.voice_retention == VoiceRetention.DELETE_ON_CLOSE
    assert sess.voice_retention == VoiceRetention.DELETE_ON_CLOSE


@pytest.mark.django_db
def test_get_set_voice_retention():
    from apps.identity.models import Account, VoiceRetention
    from apps.identity.services import Actor, get_voice_retention, set_voice_retention

    acc = Account.objects.create_user(email="vr2@ex.com", password="password123")
    actor = Actor(kind="account", account=acc)
    assert get_voice_retention(actor) == VoiceRetention.DELETE_ON_CLOSE
    assert set_voice_retention(actor, "keep") == "keep"
    acc.refresh_from_db()
    assert acc.voice_retention == VoiceRetention.KEEP


@pytest.mark.django_db
def test_voice_retention_api():
    from django.test import Client

    from apps.identity.models import Account

    acc = Account.objects.create_user(email="vr-api@ex.com", password="password123")
    client = Client()
    client.force_login(acc)
    got = client.get("/api/v1/me/voice-retention")
    assert got.status_code == 200
    assert got.json()["voice_retention"] == "delete_on_close"
    put = client.post(
        "/api/v1/me/voice-retention",
        data={"voice_retention": "keep"},
        content_type="application/json",
    )
    assert put.status_code == 200
    assert put.json()["voice_retention"] == "keep"
    acc.refresh_from_db()
    assert acc.voice_retention == "keep"


@pytest.mark.django_db
def test_register_login_me_logout_http():
    from django.test import Client

    client = Client()
    reg = client.post(
        "/api/v1/auth/register",
        data={
            "email": "http-user@ex.com",
            "password": "password123",
            "pseudonym": "тихий",
        },
        content_type="application/json",
    )
    assert reg.status_code == 200
    assert reg.json()["email"] == "http-user@ex.com"
    me = client.get("/api/v1/me")
    assert me.json()["is_authenticated"] is True
    client.post("/api/v1/auth/logout")
    login = client.post(
        "/api/v1/auth/login",
        data={"email": "http-user@ex.com", "password": "password123"},
        content_type="application/json",
    )
    assert login.status_code == 200
    bad = client.post(
        "/api/v1/auth/login",
        data={"email": "http-user@ex.com", "password": "wrong-wrong"},
        content_type="application/json",
    )
    assert bad.status_code == 400
