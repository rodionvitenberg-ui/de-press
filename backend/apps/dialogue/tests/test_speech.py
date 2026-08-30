"""AITranslator dedicated URL vs gateway/offline fallback."""

from __future__ import annotations

from types import SimpleNamespace

from apps.dialogue.speech import (
    AITranslator,
    OfflineTranslator,
)


class _FakeCompletions:
    def __init__(self, content=None, error=None):
        self._content = content
        self._error = error
        self.last = None

    def create(self, **kwargs):
        self.last = kwargs
        if self._error:
            raise self._error
        msg = SimpleNamespace(content=self._content)
        choice = SimpleNamespace(message=msg)
        return SimpleNamespace(choices=[choice])


def _patch_openai(monkeypatch, content=None, error=None):
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=_FakeCompletions(content, error))
    )

    def factory(**kwargs):
        factory.kwargs = kwargs  # type: ignore[attr-defined]
        return fake_client

    factory.kwargs = None  # type: ignore[attr-defined]
    factory.client = fake_client  # type: ignore[attr-defined]
    monkeypatch.setattr("openai.OpenAI", factory)
    return factory


def test_dedicated_translator_url_used(monkeypatch, settings):
    settings.TRANSLATOR_BASE_URL = "http://translator.test/v1"
    settings.TRANSLATOR_MODEL = "Hy-MT1.5-1.8B"
    settings.TRANSLATOR_API_KEY = "sk-test"
    factory = _patch_openai(monkeypatch, content="Hello there")
    out = AITranslator().translate("Привет", target_lang="en", source_lang="ru")
    assert out == "Hello there"
    assert factory.kwargs["base_url"] == "http://translator.test/v1"
    assert factory.kwargs["api_key"] == "sk-test"


def test_dedicated_uses_mt_template_without_system_prompt(monkeypatch, settings):
    settings.TRANSLATOR_BASE_URL = "http://translator.test/v1"
    settings.TRANSLATOR_MODEL = "mt-model"
    factory = _patch_openai(monkeypatch, content="Кормить")
    translator = AITranslator()
    assert translator.translate("Feed", target_lang="ru") == "Кормить"
    created = factory.client.chat.completions.last
    assert [m["role"] for m in created["messages"]] == ["user"]
    assert created["messages"][0]["content"] == (
        "Translate the following segment into Russian, "
        "without additional explanation.\n\nFeed"
    )
    assert created["temperature"] == 0.7


def test_dedicated_zh_target_uses_chinese_template(monkeypatch, settings):
    settings.TRANSLATOR_BASE_URL = "http://translator.test/v1"
    factory = _patch_openai(monkeypatch, content="喂")
    assert AITranslator().translate("Feed", target_lang="zh") == "喂"
    content = factory.client.chat.completions.last["messages"][0]["content"]
    assert content == "把下面的文本翻译成中文，不要额外解释。\n\nFeed"


def test_dedicated_translator_unreachable_falls_back_offline(monkeypatch, settings):
    settings.TRANSLATOR_BASE_URL = "http://127.0.0.1:9/v1"
    settings.TRANSLATOR_MODEL = "Hy-MT1.5-1.8B"
    settings.TRANSLATOR_API_KEY = ""
    settings.AI_API_KEY = ""
    _patch_openai(monkeypatch, error=ConnectionError("down"))
    out = AITranslator().translate("Привет", target_lang="en", source_lang="ru")
    assert out == OfflineTranslator().translate(
        "Привет", target_lang="en", source_lang="ru"
    )


def test_empty_translator_url_skips_openai_client(monkeypatch, settings):
    settings.TRANSLATOR_BASE_URL = ""
    settings.AI_API_KEY = ""
    called = {"n": 0}

    def factory(**kwargs):
        called["n"] += 1
        raise AssertionError("OpenAI client must not be built when URL is empty")

    monkeypatch.setattr("openai.OpenAI", factory)
    out = AITranslator().translate("Я рядом", target_lang="en", source_lang="ru")
    assert called["n"] == 0
    assert out.startswith("[offline en]")
