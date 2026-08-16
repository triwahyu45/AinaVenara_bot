import asyncio
from collections import deque

from aina_companion.audio import pcm_rms_levels
import json

import pytest

from aina_companion.avatar import AvatarHub, UnityAvatarLauncher, avatar_event


def test_avatar_event_schema():
    assert avatar_event("emotion", value="marah", intensity=0.8) == {
        "type": "emotion",
        "value": "marah",
        "intensity": 0.8,
    }


def test_pcm_rms_levels_detect_silence_and_audio():
    silence = b"\x00\x00" * 1200
    loud = b"\xff\x2e" * 1200
    assert pcm_rms_levels(silence) == [0.0]
    assert pcm_rms_levels(loud)[0] > 0.5


def test_unity_launcher_returns_false_for_missing_executable(tmp_path):
    launcher = UnityAvatarLauncher(str(tmp_path / "missing.exe"))
    assert launcher.launch() is False


def test_avatar_hub_queues_message_without_renderer():
    hub = AvatarHub.__new__(AvatarHub)
    hub.clients = set()
    hub.pending = deque(maxlen=100)
    asyncio.run(hub._broadcast('{"type":"state","value":"thinking"}'))
    assert list(hub.pending) == ['{"type":"state","value":"thinking"}']


def test_avatar_event_rejects_unknown_state_emotion_and_fps():
    with pytest.raises(ValueError, match="State avatar"):
        avatar_event("state", value="sleeping")
    with pytest.raises(ValueError, match="Emosi avatar"):
        avatar_event("emotion", value="lapar")
    with pytest.raises(ValueError, match="FPS avatar"):
        avatar_event("config", fps=144)


def test_audio_level_is_clamped():
    assert avatar_event("audio_level", value=5)["value"] == 1
    assert avatar_event("audio_level", value=-1)["value"] == 0


def test_reconnect_queue_keeps_latest_replaceable_event():
    hub = AvatarHub.__new__(AvatarHub)
    hub.pending = deque(maxlen=100)
    hub._queue(json.dumps(avatar_event("audio_level", value=0.2)))
    hub._queue(json.dumps(avatar_event("audio_level", value=0.8)))
    hub._queue(json.dumps(avatar_event("state", value="thinking")))
    hub._queue(json.dumps(avatar_event("state", value="speaking")))

    queued = [json.loads(raw) for raw in hub.pending]
    assert queued == [
        {"type": "audio_level", "value": 0.8},
        {"type": "state", "value": "speaking"},
    ]


def test_launcher_uses_hidden_process_flag_on_windows(tmp_path, monkeypatch):
    executable = tmp_path / "renderer.exe"
    executable.touch()
    calls = []
    monkeypatch.setattr("aina_companion.avatar.os.name", "nt")
    monkeypatch.setattr("aina_companion.avatar.subprocess.CREATE_NO_WINDOW", 123, raising=False)
    monkeypatch.setattr(
        "aina_companion.avatar.subprocess.Popen",
        lambda *args, **kwargs: calls.append((args, kwargs)) or object(),
    )

    assert UnityAvatarLauncher(str(executable)).launch() is True
    assert calls[0][1]["creationflags"] == 123
