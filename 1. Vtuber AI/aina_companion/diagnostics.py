from __future__ import annotations

import asyncio
import importlib.util
from typing import Any


def module_available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


def dependency_report() -> list[str]:
    checks = {
        "PySide6": "PySide6",
        "Google GenAI": "google.genai",
        "Credential Manager": "keyring",
        "Google Cloud STT": "google.cloud.speech",
        "Audio playback": "pygame",
        "Unity WebSocket IPC": "websockets",
    }
    return [
        f"{label}: {'OK' if module_available(module) else 'BELUM TERPASANG'}"
        for label, module in checks.items()
    ]
def run_async(coroutine) -> Any:
    return asyncio.run(coroutine)
