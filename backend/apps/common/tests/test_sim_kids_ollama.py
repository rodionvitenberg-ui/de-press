from __future__ import annotations

import httpx

from apps.common.kids import ollama as ollama_mod


def test_complete_returns_text(monkeypatch, settings):
    settings.KIDS_BASE_URL = "http://ollama.test/v1"
    settings.KIDS_MODEL = "qwen2.5:0.5b"
    settings.KIDS_API_KEY = "k"

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "  тихо.  "}}]}

    def fake_post(url, **kwargs):
        assert url.endswith("/chat/completions")
        return _Resp()

    monkeypatch.setattr(ollama_mod.httpx, "post", fake_post)
    assert ollama_mod.complete("скажи") == "тихо."


def test_complete_empty_base(settings):
    settings.KIDS_BASE_URL = ""
    assert ollama_mod.complete("x") == ""


def test_complete_swallows_errors(monkeypatch, settings):
    settings.KIDS_BASE_URL = "http://ollama.test/v1"

    def boom(*args, **kwargs):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(ollama_mod.httpx, "post", boom)
    assert ollama_mod.complete("x") == ""
