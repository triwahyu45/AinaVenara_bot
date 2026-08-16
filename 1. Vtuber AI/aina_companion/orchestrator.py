from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .avatar import avatar_event
from .gemini import ChatReply


@dataclass
class ConversationResult:
    reply: ChatReply
    summary_updated: bool = False


class ConversationOrchestrator:
    """Coordinates one conversation turn without depending on the UI toolkit."""

    def __init__(
        self,
        *,
        memory: Any,
        gemini: Any,
        avatar_hub: Any,
        settings: dict[str, Any],
        session_id: str,
    ):
        self.memory = memory
        self.gemini = gemini
        self.avatar_hub = avatar_hub
        self.settings = settings
        self.session_id = session_id

    def process_text(self, text: str) -> ConversationResult:
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Pesan tidak boleh kosong.")
        self.avatar_hub.send(avatar_event("state", value="thinking"))
        memory_settings = self.settings["memory"]
        context = self.memory.context(self.session_id, memory_settings["recent_message_limit"])
        reply = self.gemini.chat(clean_text, context)
        self.memory.add_message(self.session_id, "user", clean_text)
        self.memory.add_message(self.session_id, "model", reply.raw_text)
        summary_updated = self._update_summary_if_needed(memory_settings["summary_trigger"])
        self.avatar_hub.send(
            avatar_event("emotion", value=reply.emotion, intensity=0.8, duration_ms=3500)
        )
        subtitle = reply.subtitle or reply.text
        self.avatar_hub.send(
            avatar_event("subtitle", text=subtitle, duration_ms=max(2500, len(subtitle) * 55))
        )
        return ConversationResult(reply=reply, summary_updated=summary_updated)

    def _update_summary_if_needed(self, trigger: int) -> bool:
        count = self.memory.message_count(self.session_id)
        if trigger <= 0 or count % trigger:
            return False
        summary = self.gemini.summarize(
            self.memory.summary(self.session_id),
            self.memory.recent_messages(self.session_id, 12),
        )
        self.memory.set_summary(self.session_id, summary)
        return True

    def speak(self, text: str, emotion: str, audio_player: Any) -> float:
        pcm = self.gemini.synthesize(text, emotion)
        self.avatar_hub.send(avatar_event("state", value="speaking"))
        duration = audio_player.play_pcm(
            pcm,
            lambda level: self.avatar_hub.send(avatar_event("audio_level", value=level)),
        )
        self.avatar_hub.send(avatar_event("state", value="idle"))
        return duration
