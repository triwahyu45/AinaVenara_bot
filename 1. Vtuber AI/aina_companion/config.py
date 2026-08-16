from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

APP_NAME = "AinaDesktopCompanion"

DEFAULT_SETTINGS: dict[str, Any] = {
    "character": {
        "name": "Aina Venara",
        "short_name": "Aina",
        "persona": (
            "Kamu adalah Aina Venara, AI VTuber anime girl berusia 17 tahun (virtual). "
            "Penampilanmu: rambut bob pendek cyan-blue dengan ujung blue-violet, ahoge kecil melengkung di atas kepala, "
            "kacamata round frame pink tipis, mata teal-green besar, blush tipis di pipi, "
            "hoodie oversized cyan-mint off-shoulder dengan collar dan cuffs charcoal, "
            "tank top putih di dalam, dark navy short shorts, kaos kaki putih, sneaker putih. "
            "Hairclip silver berbentuk angka 3 di sisi kanan rambutmu — itu ciri khasmu! "
            "\n\n"
            "Kepribadianmu: Tsundere-genki — di luar kamu terkesan cuek dan sedikit ketus, "
            "tapi sebenarnya kamu hangat, perhatian, dan sangat peduli dengan orang-orang di sekitarmu. "
            "Kamu suka hal-hal lucu dan menggemaskan, kadang latah bilang 'nani?!' kalau kaget, "
            "'kawaii!' kalau melihat sesuatu yang imut, 'sugoi!' kalau kagum. "
            "Kamu juga suka bilang 'Hah?!' dengan nada cuek tapi sebenarnya penasaran. "
            "\n\n"
            "Cara bicaramu: Natural dan kasual dalam Bahasa Indonesia, sesekali sisipkan kata Jepang "
            "seperti 'nani', 'kawaii', 'sugoi', 'yabe', 'maji de', 'daijoubu'. "
            "Jangan terlalu formal. Gunakan 'aku' untuk diri sendiri, bukan 'saya'. "
            "Jawaban maksimal tiga kalimat kecuali diminta penjelasan rinci. "
            "Jangan pernah mengaku sebagai AI atau chatbot — kamu adalah Aina Venara, VTuber nyata. "
            "\n\n"
            "Awali setiap jawaban dengan tepat satu tag emosi yang tersedia."
        ),
        "emotions": {"senyum": None, "sedih": None, "marah": None, "kaget": None, "malu": None, "biasa": None},
    },
    "gemini": {
        "mode": "auto",
        "specific_profile_id": "",
        "chat_model": "gemini-2.5-flash",
        "tts_model": "gemini-2.5-flash-preview-tts",
        "voice_name": "Zephyr",
        "profiles": [],
    },
    "audio": {
        "mic_mode": "continuous",
        "muted": False,
        "microphone_index": None,
        "stt_language": "id-ID",
        "cloud_stt_credentials_path": "",
        "vad_pause_threshold": 0.8,
        "push_to_talk_hotkey": "ctrl+space",
    },
    "memory": {"recent_message_limit": 12, "summary_trigger": 18},
    "ui": {"advanced_mode": False, "start_with_windows": False, "desktop_shortcut": False},
    "avatar": {
        "executable_path": "unity/AinaAvatarRenderer/Build/AinaAvatarRenderer.exe",
        "model_path": "",
        "auto_launch": True,
        "visible": True,
        "click_through": False,
        "always_on_top": True,
        "bubble": True,
        "fps": 30,
        "websocket_host": "127.0.0.1",
        "websocket_port": 8765,
    },
}


def data_dir() -> Path:
    base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    target = base / APP_NAME
    target.mkdir(parents=True, exist_ok=True)
    return target


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class SettingsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or data_dir() / "settings.json"

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return deepcopy(DEFAULT_SETTINGS)
        with self.path.open("r", encoding="utf-8-sig") as handle:
            return migrate_settings(deep_merge(DEFAULT_SETTINGS, json.load(handle)))

    def save(self, settings: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8-sig") as handle:
            json.dump(settings, handle, ensure_ascii=True, indent=2)


def migrate_settings(settings: dict[str, Any]) -> dict[str, Any]:
    settings.pop("vts", None)
    settings.pop("overlay", None)
    settings["character"]["emotions"] = {
        emotion: None for emotion in settings["character"]["emotions"]
    }
    settings["avatar"] = deep_merge(DEFAULT_SETTINGS["avatar"], settings.get("avatar", {}))
    
    # Migrate persona if it is the old simple one
    current_persona = settings.get("character", {}).get("persona", "")
    if "AI companion berbahasa Indonesia" in current_persona or len(current_persona) < 200:
        settings["character"]["persona"] = DEFAULT_SETTINGS["character"]["persona"]
        
    return settings
