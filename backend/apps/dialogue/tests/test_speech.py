"""AITranslator dedicated URL vs gateway/offline fallback."""

from __future__ import annotations

from types import SimpleNamespace

from apps.dialogue.speech import (
    AITranslator,
    OfflineTranslator,
    OpenAICompatibleTTS,
    get_tts,
)


class _FakeCompletions:
    def __init__(self, content=None, error=None):
        self._content = content
        self._error = error

    def create(self, **kwargs):
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


def test_get_tts_none_without_key(settings):
    settings.TTS_API_KEY = ""
    settings.AI_API_KEY = ""
    assert get_tts() is None


def test_get_tts_builds_adapter_from_settings(settings):
    settings.TTS_API_KEY = "sk-tts"
    settings.TTS_BASE_URL = "http://tts.test/v1"
    settings.TTS_MODEL = "tts-1"
    adapter = get_tts()
    assert isinstance(adapter, OpenAICompatibleTTS)


def test_openai_tts_synthesize_posts_speech(monkeypatch):
    captured = {}

    class _FakeResp:
        status_code = 200
        content = b"MP3BYTES"

        def raise_for_status(self):
            return None

    class _FakeClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, **kwargs):
            captured["url"] = url
            captured["headers"] = kwargs.get("headers")
            captured["json"] = kwargs.get("json")
            return _FakeResp()

    monkeypatch.setattr("httpx.Client", _FakeClient)
    tts = OpenAICompatibleTTS(
        api_key="sk-tts", base_url="http://tts.test/v1/", model="tts-1"
    )
    out = tts.synthesize("Привет", lang="ru")
    assert out == b"MP3BYTES"
    assert captured["url"] == "http://tts.test/v1/audio/speech"
    assert captured["headers"]["Authorization"] == "Bearer sk-tts"
    assert captured["json"]["input"] == "Привет"
    assert captured["json"]["response_format"] == "mp3"
