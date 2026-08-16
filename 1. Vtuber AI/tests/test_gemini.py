from types import SimpleNamespace

import pytest

from aina_companion.config import DEFAULT_SETTINGS
from aina_companion.gemini import GeminiService, UnsupportedModelError, parse_chat_reply
from aina_companion.profiles import ApiProfile, ApiProfileManager


class FakeModels:
    def __init__(self):
        self.responses = []
        self.calls = []
        self.available = [
            SimpleNamespace(
                name="models/gemini-2.5-flash",
                display_name="Gemini 2.5 Flash",
                supported_actions=["generateContent"],
            ),
            SimpleNamespace(
                name="models/gemini-2.5-flash-preview-tts",
                display_name="Gemini 2.5 Flash Preview TTS",
                supported_actions=["generateContent"],
            ),
            SimpleNamespace(
                name="models/embed-content",
                display_name="Embedding",
                supported_actions=["embedContent"],
            ),
        ]

    def list(self):
        return self.available

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeClient:
    def __init__(self):
        self.models = FakeModels()


def service(fake_client):
    manager = ApiProfileManager([ApiProfile("profile", "Primary")], lambda _profile_id: "secret")
    return GeminiService(DEFAULT_SETTINGS, manager, client_factory=lambda _key: fake_client)


def test_available_models_filters_chat_and_tts_capabilities():
    gemini = service(FakeClient())
    assert [model.name for model in gemini.available_models("secret", "chat")] == [
        "gemini-2.5-flash"
    ]
    assert [model.name for model in gemini.available_models("secret", "tts")] == [
        "gemini-2.5-flash-preview-tts"
    ]


def test_validate_model_rejects_unknown_model():
    gemini = service(FakeClient())
    with pytest.raises(UnsupportedModelError, match="tidak tersedia"):
        gemini.validate_model("secret", "gemini-3.5-magic", "chat")


def test_chat_requests_json_and_parses_structured_reply():
    client = FakeClient()
    client.models.responses.append(
        SimpleNamespace(text='{"text":"Halo.","subtitle":"Halo!","emotion":"senyum"}')
    )
    gemini = service(client)

    reply = gemini.chat(
        "Hai",
        {"facts": ["User suka kopi."], "summary": "Sudah kenal.", "messages": []},
    )

    assert reply.text == "Halo."
    assert reply.subtitle == "Halo!"
    assert reply.emotion == "senyum"
    request = client.models.calls[0]
    assert request["model"] == "gemini-2.5-flash"
    assert request["config"].response_mime_type == "application/json"
    assert "User suka kopi." in request["contents"][0]["parts"][0]["text"]


def test_chat_parser_keeps_legacy_tag_fallback():
    reply = parse_chat_reply("[Marah] Jangan begitu.")
    assert (reply.emotion, reply.text, reply.subtitle) == (
        "marah",
        "Jangan begitu.",
        "Jangan begitu.",
    )


def test_synthesize_returns_pcm_bytes():
    client = FakeClient()
    audio = b"\x00\x01\x02"
    inline_data = SimpleNamespace(data=audio)
    part = SimpleNamespace(inline_data=inline_data)
    content = SimpleNamespace(parts=[part])
    client.models.responses.append(SimpleNamespace(candidates=[SimpleNamespace(content=content)]))

    assert service(client).synthesize("Halo") == audio


def test_summarize_uses_configured_chat_model():
    client = FakeClient()
    client.models.responses.append(SimpleNamespace(text="Ringkas."))
    result = service(client).summarize("", [{"role": "user", "content": "Halo"}])
    assert result == "Ringkas."
    assert client.models.calls[0]["model"] == "gemini-2.5-flash"


def test_client_is_kept_open_until_request_finishes_then_closed():
    events = []

    class LifecycleModels:
        def generate_content(self, **_kwargs):
            events.append("request")
            return SimpleNamespace(text="OK")

    class LifecycleClient:
        def __init__(self):
            self.models = LifecycleModels()

        def close(self):
            events.append("close")

    manager = ApiProfileManager([ApiProfile("profile", "Primary")], lambda _profile_id: "secret")
    gemini = GeminiService(DEFAULT_SETTINGS, manager, client_factory=lambda _key: LifecycleClient())

    assert gemini.test_key("secret") == "OK"
    assert events == ["request", "close"]
