from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Iterator

from .emotion import emotion_prompt, parse_emotion
from .profiles import ApiProfileManager

CHAT_ACTION = "generateContent"
EMOTIONS = {"biasa", "senyum", "sedih", "malu", "kaget", "marah"}


class UnsupportedModelError(ValueError):
    pass


@dataclass(frozen=True)
class ModelOption:
    name: str
    display_name: str
    supported_actions: tuple[str, ...]


@dataclass
class ChatReply:
    emotion: str
    text: str
    raw_text: str
    subtitle: str = ""


def normalize_model_name(name: str) -> str:
    return name.removeprefix("models/")


def parse_chat_reply(raw_text: str, valid_emotions: set[str] | None = None) -> ChatReply:
    allowed = valid_emotions or EMOTIONS
    try:
        value = json.loads(raw_text)
    except (TypeError, json.JSONDecodeError):
        emotion, text = parse_emotion(raw_text, allowed)
        return ChatReply(emotion=emotion, text=text, subtitle=text, raw_text=raw_text)

    if not isinstance(value, dict):
        emotion, text = parse_emotion(raw_text, allowed)
        return ChatReply(emotion=emotion, text=text, subtitle=text, raw_text=raw_text)
    text = str(value.get("text", "")).strip()
    if not text:
        emotion, text = parse_emotion(raw_text, allowed)
        return ChatReply(emotion=emotion, text=text, subtitle=text, raw_text=raw_text)
    emotion = str(value.get("emotion", "biasa")).strip().lower()
    if emotion not in allowed:
        emotion = "biasa"
    subtitle = str(value.get("subtitle", text)).strip() or text
    return ChatReply(emotion=emotion, text=text, subtitle=subtitle, raw_text=raw_text)


class GeminiService:
    def __init__(
        self,
        settings: dict[str, Any],
        profiles: ApiProfileManager,
        client_factory: Callable[[str], Any] | None = None,
    ):
        self.settings = settings
        self.profiles = profiles
        self.client_factory = client_factory or self._client

    @staticmethod
    def _client(api_key: str):
        from google import genai

        return genai.Client(api_key=api_key)

    @contextmanager
    def _client_scope(self, api_key: str) -> Iterator[Any]:
        client = self.client_factory(api_key)
        try:
            yield client
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

    def available_models(self, api_key: str, capability: str = "chat") -> list[ModelOption]:
        if capability not in {"chat", "tts"}:
            raise ValueError(f"Capability model tidak dikenal: {capability}")
        options: list[ModelOption] = []
        with self._client_scope(api_key) as client:
            for model in client.models.list():
                name = normalize_model_name(str(model.name))
                actions = tuple(model.supported_actions or ())
                if CHAT_ACTION not in actions:
                    continue
                if capability == "tts" and not name.endswith("-tts"):
                    continue
                if capability == "chat" and name.endswith("-tts"):
                    continue
                options.append(
                    ModelOption(
                        name=name,
                        display_name=str(model.display_name or name),
                        supported_actions=actions,
                    )
                )
        return sorted(options, key=lambda option: option.name)

    def validate_model(self, api_key: str, model_name: str, capability: str = "chat") -> str:
        normalized = normalize_model_name(model_name.strip())
        available = {option.name for option in self.available_models(api_key, capability)}
        if normalized not in available:
            raise UnsupportedModelError(
                f"Model {normalized!r} tidak tersedia untuk capability {capability!r}."
            )
        return normalized

    def test_key(self, api_key: str) -> str:
        with self._client_scope(api_key) as client:
            response = client.models.generate_content(
                model=self.settings["gemini"]["chat_model"], contents="Balas tepat dengan: OK"
            )
        return response.text.strip()

    def chat(self, text: str, memory_context: dict[str, object]) -> ChatReply:
        from google.genai import types

        character = self.settings["character"]
        allowed_emotions = set(character["emotions"]) & EMOTIONS
        system_instruction = "\n".join(
            [
                character["persona"],
                emotion_prompt(character["emotions"]),
                "Aturan format respon:",
                "1. Kamu wajib merespon dalam format JSON dengan key 'text', 'subtitle', dan 'emotion'.",
                "2. Jangan pernah memasukkan tag emosi seperti '[Senyum]' atau '[Biasa]' di dalam isi string 'text' atau 'subtitle'. Pilihan emosi hanya ditentukan melalui key 'emotion' saja.",
                "3. 'text' adalah kalimat yang akan kamu ucapkan lewat suara TTS. Buat kalimat yang natural untuk diucapkan, hindari tanda baca aneh, emoji, atau simbol yang tidak perlu dibaca.",
                "4. 'subtitle' adalah teks subtitle yang muncul di layar. Biasanya sama dengan 'text', tapi boleh ditambahkan emoji jika diinginkan.",
                "5. Ingatlah bahwa kamu adalah seorang VTuber ceria dan tsundere yang sedang berinteraksi secara interaktif dengan penonton/chat livestream kamu! Jawab dengan gaya VTuber yang hidup, asyik, dan ekspresif.",
                "6. Jawaban maksimal tiga kalimat saja kecuali jika user meminta penjelasan yang sangat rinci.",
            ]
        )
        context_parts = []
        if memory_context["facts"]:
            context_parts.append("Fakta penting tentang user:\n- " + "\n- ".join(memory_context["facts"]))
        if memory_context["summary"]:
            context_parts.append("Ringkasan percakapan lama:\n" + str(memory_context["summary"]))
        contents: list[dict[str, Any]] = []
        if context_parts:
            contents.append({"role": "user", "parts": [{"text": "\n\n".join(context_parts)}]})
            contents.append({"role": "model", "parts": [{"text": "Aku mengingat konteksnya."}]})
        for message in memory_context["messages"]:
            contents.append({"role": message["role"], "parts": [{"text": message["content"]}]})
        contents.append({"role": "user", "parts": [{"text": text.strip()}]})

        def operation(api_key: str, _profile):
            with self._client_scope(api_key) as client:
                response = client.models.generate_content(
                    model=self.settings["gemini"]["chat_model"],
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                        response_mime_type="application/json",
                        response_schema={
                            "type": "OBJECT",
                            "properties": {
                                "text": {"type": "STRING"},
                                "subtitle": {"type": "STRING"},
                                "emotion": {"type": "STRING", "enum": sorted(allowed_emotions)},
                            },
                            "required": ["text", "emotion"],
                        },
                    ),
                )
            return response.text.strip()

        raw = self.profiles.call(operation)
        return parse_chat_reply(raw, allowed_emotions)

    def summarize(self, previous_summary: str, messages: list[dict[str, str]]) -> str:
        transcript = "\n".join(f"{item['role']}: {item['content']}" for item in messages)

        def operation(api_key: str, _profile):
            with self._client_scope(api_key) as client:
                response = client.models.generate_content(
                    model=self.settings["gemini"]["chat_model"],
                    contents=(
                        "Ringkas percakapan berikut dalam bahasa Indonesia. Simpan preferensi, "
                        "keputusan, dan konteks penting. Maksimal 180 kata.\n\n"
                        f"Ringkasan sebelumnya:\n{previous_summary}\n\nPesan terbaru:\n{transcript}"
                    ),
                )
            return response.text.strip()

        return self.profiles.call(operation)

    def synthesize(self, text: str, emotion: str = "biasa") -> bytes:
        from google.genai import types

        def operation(api_key: str, _profile):
            with self._client_scope(api_key) as client:
                response = client.models.generate_content(
                    model=self.settings["gemini"]["tts_model"],
                    contents=f"Bacakan dengan natural, emosi {emotion}, bahasa Indonesia: {text}",
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=self.settings["gemini"]["voice_name"]
                                )
                            )
                        ),
                    ),
                )
            data = response.candidates[0].content.parts[0].inline_data.data
            if not isinstance(data, bytes) or not data:
                raise RuntimeError("Gemini TTS tidak mengembalikan audio PCM.")
            return data

        return self.profiles.call(operation)
