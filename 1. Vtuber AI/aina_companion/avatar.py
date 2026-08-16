from __future__ import annotations

import asyncio
import json
import os
import subprocess
import threading
from collections import deque
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from .config import data_dir

SEED_SAN_URL = "https://github.com/madjin/vrm-samples/raw/refs/heads/master/Seed-san/vrm/Seed-san.vrm"
SEED_SAN_LICENSE = "https://vrm.dev/en/licenses/1.0/"
AVATAR_PATH = "/avatar"
EVENT_TYPES = {
    "state",
    "emotion",
    "audio_level",
    "subtitle",
    "config",
    "model.load",
    "animation.play",
}
AVATAR_STATES = {"idle", "thinking", "speaking"}
AVATAR_EMOTIONS = {"biasa", "senyum", "sedih", "malu", "kaget", "marah"}
REPLACEABLE_EVENTS = {"state", "audio_level", "subtitle", "config", "model.load"}


def avatar_event(event_type: str, **payload: Any) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Event avatar tidak dikenal: {event_type}")
    message = {"type": event_type, **payload}
    if event_type == "state" and payload.get("value") not in AVATAR_STATES:
        raise ValueError(f"State avatar tidak dikenal: {payload.get('value')}")
    if event_type == "emotion" and payload.get("value") not in AVATAR_EMOTIONS:
        raise ValueError(f"Emosi avatar tidak dikenal: {payload.get('value')}")
    if event_type == "audio_level":
        message["value"] = min(1.0, max(0.0, float(payload.get("value", 0.0))))
    if event_type == "config":
        fps = int(payload.get("fps", 30))
        if fps not in {30, 60}:
            raise ValueError("FPS avatar hanya mendukung 30 atau 60.")
        message["fps"] = fps
    return message


class AvatarHub:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.loop = asyncio.new_event_loop()
        self.clients: set[Any] = set()
        self.pending: deque[str] = deque(maxlen=100)
        self.last_message: dict[str, Any] | None = None
        self.last_error = ""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._serve())
        self.loop.run_forever()

    async def _serve(self) -> None:
        from websockets.asyncio.server import serve

        self.server = await serve(self._on_client, self.host, self.port)

    async def _on_client(self, websocket) -> None:
        request = getattr(websocket, "request", None)
        if request is not None and request.path != AVATAR_PATH:
            await websocket.close(1008, "Gunakan endpoint /avatar.")
            return
        self.clients.add(websocket)
        try:
            while self.pending:
                await websocket.send(self.pending.popleft())
            async for raw in websocket:
                self.last_message = json.loads(raw)
        finally:
            self.clients.discard(websocket)

    async def _broadcast(self, raw: str) -> None:
        if not self.clients:
            self._queue(raw)
            return
        for client in list(self.clients):
            try:
                await client.send(raw)
            except Exception:
                self.clients.discard(client)
                self._queue(raw)

    def _queue(self, raw: str) -> None:
        event_type = json.loads(raw).get("type")
        if event_type in REPLACEABLE_EVENTS:
            self.pending = deque(
                (
                    queued
                    for queued in self.pending
                    if json.loads(queued).get("type") != event_type
                ),
                maxlen=100,
            )
        self.pending.append(raw)

    def send(self, message: dict[str, Any]) -> None:
        raw = json.dumps(message, ensure_ascii=True)
        asyncio.run_coroutine_threadsafe(self._broadcast(raw), self.loop)

    def connected(self) -> bool:
        return bool(self.clients)

    def close(self) -> None:
        if hasattr(self, "server"):
            self.loop.call_soon_threadsafe(self.server.close)
        self.loop.call_soon_threadsafe(self.loop.stop)


class UnityAvatarLauncher:
    def __init__(self, executable_path: str):
        self.executable_path = executable_path
        self.process: subprocess.Popen | None = None

    def launch(self) -> bool:
        path = Path(self.executable_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[1] / path
        if not path.exists():
            return False
        if self.process and self.process.poll() is None:
            return True
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        self.process = subprocess.Popen([str(path)], cwd=path.parent, creationflags=creationflags)
        return True

    def close(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()


def download_seed_san(target: Path | None = None) -> Path:
    destination = target or data_dir() / "models" / "Seed-san.vrm"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(SEED_SAN_URL, timeout=60) as response:
        destination.write_bytes(response.read())
    return destination
