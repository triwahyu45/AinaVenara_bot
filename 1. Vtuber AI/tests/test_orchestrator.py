from aina_companion.gemini import ChatReply
from aina_companion.memory import MemoryStore
from aina_companion.orchestrator import ConversationOrchestrator


class FakeAvatarHub:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)


class FakeGemini:
    def __init__(self):
        self.context = None
        self.summary_calls = 0

    def chat(self, text, context):
        self.context = context
        return ChatReply("senyum", f"Halo, {text}", f"Halo, {text}", "Halo!")

    def summarize(self, _previous, _messages):
        self.summary_calls += 1
        return "Ringkasan baru."

    def synthesize(self, _text, _emotion):
        return b"\x00\x00"


class FakeAudioPlayer:
    def play_pcm(self, pcm, on_level):
        assert pcm == b"\x00\x00"
        on_level(0.42)
        return 0.5


def orchestrator(tmp_path, summary_trigger=18):
    memory = MemoryStore(tmp_path / "memory.sqlite3")
    session = memory.create_session()
    avatar = FakeAvatarHub()
    gemini = FakeGemini()
    settings = {"memory": {"recent_message_limit": 12, "summary_trigger": summary_trigger}}
    return ConversationOrchestrator(
        memory=memory,
        gemini=gemini,
        avatar_hub=avatar,
        settings=settings,
        session_id=session,
    ), memory, avatar, gemini


def test_process_text_persists_turn_and_emits_avatar_events(tmp_path):
    flow, memory, avatar, gemini = orchestrator(tmp_path)
    result = flow.process_text(" Hai ")

    assert result.reply.text == "Halo, Hai"
    assert memory.message_count(flow.session_id) == 2
    assert gemini.context == {"summary": "", "facts": [], "messages": []}
    assert [event["type"] for event in avatar.messages] == ["state", "emotion", "subtitle"]
    assert avatar.messages[-1]["text"] == "Halo!"
    memory.close()


def test_process_text_refreshes_summary_at_configured_threshold(tmp_path):
    flow, memory, _avatar, gemini = orchestrator(tmp_path, summary_trigger=2)
    result = flow.process_text("Hai")
    assert result.summary_updated is True
    assert gemini.summary_calls == 1
    assert memory.summary(flow.session_id) == "Ringkasan baru."
    memory.close()


def test_speak_emits_lipsync_and_returns_to_idle(tmp_path):
    flow, memory, avatar, _gemini = orchestrator(tmp_path)
    assert flow.speak("Halo", "senyum", FakeAudioPlayer()) == 0.5
    assert avatar.messages == [
        {"type": "state", "value": "speaking"},
        {"type": "audio_level", "value": 0.42},
        {"type": "state", "value": "idle"},
    ]
    memory.close()
