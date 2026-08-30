from __future__ import annotations

import hashlib
import json

from ninja import Router, Schema
from django.conf import settings
from ninja.errors import HttpError
from django.core.cache import cache

from apps.common.i18n_ui import I18nUiError, translate_ui_strings
from apps.identity.services import resolve_actor

router = Router(tags=["i18n"])

RATE_LIMIT = 20
RATE_WINDOW = 3600
# Key already hashes the catalog contents → no staleness; a long TTL amortizes
# the slow local CPU translation (minutes per language on a cache miss).
CATALOG_TTL = 60 * 60 * 24 * 7


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
    # Privacy: a raw IP must never be stored anywhere, not even in Redis.
    # Keep only a SECRET_KEY-salted hash, usable for rate counting within TTL.
    ip = request.META.get("REMOTE_ADDR") or "anon"
    digest = hashlib.sha256(f"{settings.SECRET_KEY}:i18n-rate:{ip}".encode()).hexdigest()[:32]
    return f"i18n-ui:ip:{digest}"


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


def _catalog_key(target_lang: str, source_lang: str, strings: dict[str, str]) -> str:
    """Stable key: same source catalog + language → same translation."""
    blob = json.dumps(strings, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]
    lang = (target_lang or "").strip().lower()[:8]
    src = (source_lang or "en").strip().lower()[:8]
    return f"i18n-ui:cat:{lang}:{src}:{digest}"


@router.post("/i18n/ui-catalog", response=UiCatalogOut)
def ui_catalog(request, payload: UiCatalogIn):
    key = _catalog_key(payload.target_lang, payload.source_lang, payload.strings)
    cached = cache.get(key)
    if cached is not None:
        return UiCatalogOut(
            target_lang=payload.target_lang[:8].lower(), strings=cached
        )
    _assert_rate(request)
    try:
        strings = translate_ui_strings(
            payload.strings,
            target_lang=payload.target_lang,
            source_lang=payload.source_lang or "en",
        )
    except I18nUiError as exc:
        raise HttpError(400, str(exc)) from exc
    cache.set(key, strings, CATALOG_TTL)
    return UiCatalogOut(target_lang=payload.target_lang[:8].lower(), strings=strings)
