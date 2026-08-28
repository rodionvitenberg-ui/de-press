from __future__ import annotations

from ninja import Router, Schema
from ninja.errors import HttpError
from django.core.cache import cache

from apps.common.i18n_ui import I18nUiError, translate_ui_strings
from apps.identity.services import resolve_actor

router = Router(tags=["i18n"])

RATE_LIMIT = 20
RATE_WINDOW = 3600


class UiCatalogIn(Schema):
    target_lang: str
    source_lang: str = "en"
    strings: dict[str, str]


class UiCatalogOut(Schema):
    target_lang: str
    strings: dict[str, str]


def _rate_key(request) -> str:
    actor = resolve_actor(request)
    if actor and actor.account_id:
        return f"i18n-ui:{actor.account_id}"
    if actor and actor.session:
        return f"i18n-ui:s:{actor.session.id}"
    ip = request.META.get("REMOTE_ADDR") or "anon"
    return f"i18n-ui:ip:{ip}"


def _assert_rate(request) -> None:
    key = _rate_key(request)
    n = cache.get(key)
    if n is None:
        cache.set(key, 1, RATE_WINDOW)
        return
    if int(n) >= RATE_LIMIT:
        raise HttpError(429, "Too many language loads")
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, RATE_WINDOW)


@router.post("/i18n/ui-catalog", response=UiCatalogOut)
def ui_catalog(request, payload: UiCatalogIn):
    _assert_rate(request)
    try:
        strings = translate_ui_strings(
            payload.strings,
            target_lang=payload.target_lang,
            source_lang=payload.source_lang or "en",
        )
    except I18nUiError as exc:
        raise HttpError(400, str(exc)) from exc
    return UiCatalogOut(target_lang=payload.target_lang[:8].lower(), strings=strings)
