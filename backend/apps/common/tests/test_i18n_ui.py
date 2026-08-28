from __future__ import annotations

import json

import pytest

from apps.common.i18n_ui import I18nUiError, translate_ui_strings


class _Echo:
    def translate(self, text: str, *, target_lang: str, source_lang: str = "") -> str:
        start = text.find('{"')
        end = text.rfind("}")
        blob = text[start : end + 1]
        data = json.loads(blob)
        return json.dumps({k: f"DE:{v}" for k, v in data.items()}, ensure_ascii=False)


def test_translate_ui_strings_keeps_keys(monkeypatch):
    monkeypatch.setattr("apps.common.i18n_ui.get_translator", lambda: _Echo())
    out = translate_ui_strings(
        {"nav.feed": "Feed", "nav.panic": "I'm not ok"},
        target_lang="de",
        source_lang="en",
    )
    assert out["nav.feed"] == "DE:Feed"
    assert out["nav.panic"] == "DE:I'm not ok"


def test_translate_rejects_handwritten_target():
    with pytest.raises(I18nUiError):
        translate_ui_strings({"a": "b"}, target_lang="ru")


def test_translate_rejects_empty():
    with pytest.raises(I18nUiError):
        translate_ui_strings({}, target_lang="de")
