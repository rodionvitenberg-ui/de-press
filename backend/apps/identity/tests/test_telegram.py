from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, override_settings

from apps.identity.models import Account
from apps.identity.services import AuthError
from apps.identity.telegram import (
    login_or_register_telegram,
    validate_init_data,
)


BOT_TOKEN = "123456:ABC-DEF_test_token"


def _sign_init_data(fields: dict[str, str], token: str = BOT_TOKEN) -> str:
    """Build a valid initData query string for tests."""
    pairs = dict(fields)
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    pairs["hash"] = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(pairs)


def _user_json(**overrides) -> str:
    base = {
        "id": 42,
        "first_name": "Тихий",
        "username": "quiet_user",
        "language_code": "ru",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=False)


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN)
def test_validate_init_data_ok():
    auth_date = int(time.time())
    init = _sign_init_data(
        {
            "auth_date": str(auth_date),
            "user": _user_json(),
            "query_id": "AAE",
        }
    )
    validated = validate_init_data(init, now=auth_date + 10)
    assert validated.user.id == 42
    assert validated.user.first_name == "Тихий"
    assert validated.user.username == "quiet_user"
    assert validated.query_id == "AAE"


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN)
def test_validate_init_data_bad_hash():
    auth_date = int(time.time())
    init = _sign_init_data(
        {
            "auth_date": str(auth_date),
            "user": _user_json(),
        }
    )
    # Tamper hash after signing
    init = init.rsplit("hash=", 1)[0] + "hash=" + ("0" * 64)
    with pytest.raises(AuthError, match="signature"):
        validate_init_data(init, now=auth_date + 1)


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN)
def test_validate_init_data_expired():
    auth_date = int(time.time()) - 60 * 60 * 48
    init = _sign_init_data(
        {
            "auth_date": str(auth_date),
            "user": _user_json(),
        }
    )
    with pytest.raises(AuthError, match="expired"):
        validate_init_data(init, now=int(time.time()))


@override_settings(TELEGRAM_BOT_TOKEN="")
def test_validate_not_configured():
    with pytest.raises(AuthError, match="not configured"):
        validate_init_data("hash=abc")


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN)
def test_login_or_register_creates_and_reuses():
    rf = RequestFactory()
    request = rf.post("/api/v1/auth/telegram")
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    request.user = AnonymousUser()

    auth_date = int(time.time())
    init = _sign_init_data(
        {
            "auth_date": str(auth_date),
            "user": _user_json(id=99, first_name="Саша"),
        }
    )

    account1 = login_or_register_telegram(init_data=init, request=request)
    assert account1.telegram_id == 99
    assert account1.default_pseudonym == "Саша"
    assert account1.email == "tg99@users.de-press.local"
    assert not account1.has_usable_password()
    assert Account.objects.filter(telegram_id=99).count() == 1

    request2 = rf.post("/api/v1/auth/telegram")
    middleware.process_request(request2)
    request2.session.save()
    request2.user = AnonymousUser()
    account2 = login_or_register_telegram(init_data=init, request=request2)
    assert account2.id == account1.id
    assert Account.objects.filter(telegram_id=99).count() == 1
