"""Translate flattened UI chrome strings. Never used for user content."""

from __future__ import annotations

import json
import logging
import re

from apps.dialogue.speech import get_translator, is_stub_translation

logger = logging.getLogger(__name__)

MAX_KEYS = 500
CHUNK = 500

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.I | re.M)


class I18nUiError(Exception):
    pass


def translate_ui_strings(
    strings: dict[str, str],
    *,
    target_lang: str,
    source_lang: str = "en",
) -> dict[str, str]:
    if not strings:
        raise I18nUiError("Empty catalog")
    if len(strings) > MAX_KEYS:
        raise I18nUiError("Catalog too large")
    target = (target_lang or "")[:8].lower()
    if not target or target in {"ru", "en"}:
        raise I18nUiError("target_lang must be a machine locale")
    source = (source_lang or "en")[:8].lower() or "en"

    translator = get_translator()
    keys = list(strings.keys())
    out: dict[str, str] = {}
    for i in range(0, len(keys), CHUNK):
        chunk = {k: strings[k] for k in keys[i : i + CHUNK]}
        blob = json.dumps(chunk, ensure_ascii=False)
        prompt = (
            f"Translate JSON object values to language '{target}' (source '{source}'). "
            "Keep the same keys. Do not translate tokens like {count}. "
            "Output a JSON object only.\n\n"
            f"{blob}"
        )
        raw = translator.translate(prompt, target_lang=target, source_lang=source)
        if not raw or is_stub_translation(raw):
            raise I18nUiError("Перевод сейчас недоступен")
        parsed = _parse_json_object(raw)
        for k, v in parsed.items():
            if k in chunk and isinstance(v, str) and v.strip():
                out[k] = v
    return {k: out.get(k) or strings[k] for k in strings}


def _parse_json_object(raw: str) -> dict:
    text = _FENCE.sub("", raw.strip())
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(text[start : end + 1])
        else:
            raise I18nUiError("Bad translator JSON") from exc
    if not isinstance(data, dict):
        raise I18nUiError("Bad translator JSON")
    return data
