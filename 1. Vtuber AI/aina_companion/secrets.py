from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

SERVICE_NAME = "AinaDesktopCompanion/Gemini"


class SecretBackend(Protocol):
    def get_password(self, service: str, username: str) -> str | None: ...
    def set_password(self, service: str, username: str, password: str) -> None: ...
    def delete_password(self, service: str, username: str) -> None: ...


class KeyringSecretStore:
    def __init__(self, backend: SecretBackend | None = None):
        if backend is None:
            import keyring

            backend = keyring
        self.backend = backend

    def get(self, profile_id: str) -> str | None:
        return self.backend.get_password(SERVICE_NAME, profile_id)

    def set(self, profile_id: str, api_key: str) -> None:
        value = api_key.strip()
        if not value:
            raise ValueError("API key tidak boleh kosong.")
        self.backend.set_password(SERVICE_NAME, profile_id, value)

    def delete(self, profile_id: str) -> None:
        try:
            self.backend.delete_password(SERVICE_NAME, profile_id)
        except Exception:
            pass

    def import_env(self, env_path: Path) -> list[tuple[str, str]]:
        if not env_path.exists():
            return []
        imported: list[tuple[str, str]] = []
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip().startswith("GEMINI_API_KEY") and value.strip():
                imported.append((name.strip(), value.strip()))
        return imported


class MemorySecretBackend:
    def __init__(self):
        self.values: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.values.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.values[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self.values.pop((service, username), None)

