from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Callable

RETRY_RE = re.compile(r"(?:retry(?:\s+in|Delay)?[:=]?\s*)(\d+(?:\.\d+)?)\s*s", re.I)


@dataclass
class ApiProfile:
    id: str
    label: str
    enabled: bool = True
    priority: int = 100
    cooldown_until: float = 0.0
    last_error: str = ""
    health_status: str = "unknown"

    @classmethod
    def create(cls, label: str, priority: int = 100) -> "ApiProfile":
        return cls(id=uuid.uuid4().hex, label=label.strip() or "Gemini API", priority=priority)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ApiProfile":
        allowed = {key: value[key] for key in cls.__dataclass_fields__ if key in value}
        return cls(**allowed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "enabled": self.enabled,
            "priority": self.priority,
            "cooldown_until": self.cooldown_until,
            "last_error": self.last_error,
            "health_status": self.health_status,
        }


def retry_delay_seconds(error: Exception, default: float = 60.0) -> float:
    retry_delay = getattr(error, "retry_delay", None)
    if isinstance(retry_delay, timedelta):
        return retry_delay.total_seconds()
    if isinstance(retry_delay, (int, float)):
        return float(retry_delay)
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {})
    retry_after = headers.get("retry-after") if headers else None
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass
    match = RETRY_RE.search(str(error))
    return float(match.group(1)) if match else default


def is_quota_error(error: Exception) -> bool:
    text = str(error).lower()
    return "429" in text or "resource_exhausted" in text or "quota" in text


class ApiProfileManager:
    def __init__(
        self,
        profiles: list[ApiProfile],
        secret_getter: Callable[[str], str | None],
        mode: str = "auto",
        specific_profile_id: str = "",
        now: Callable[[], float] = time.time,
        state_changed: Callable[[], None] | None = None,
    ):
        self.profiles = profiles
        self.secret_getter = secret_getter
        self.mode = mode
        self.specific_profile_id = specific_profile_id
        self.now = now
        self.state_changed = state_changed or (lambda: None)

    def candidates(self) -> list[ApiProfile]:
        if self.mode == "specific":
            current = self.now()
            return [
                profile
                for profile in self.profiles
                if profile.id == self.specific_profile_id
                and profile.enabled
                and profile.cooldown_until <= current
            ]
        current = self.now()
        return sorted(
            (
                profile
                for profile in self.profiles
                if profile.enabled and profile.cooldown_until <= current
            ),
            key=lambda profile: (profile.priority, profile.label.lower()),
        )

    def call(self, operation: Callable[[str, ApiProfile], Any]) -> Any:
        candidates = self.candidates()
        if not candidates:
            raise RuntimeError("Tidak ada Gemini API profile sehat yang tersedia.")
        last_error: Exception | None = None
        for profile in candidates:
            secret = self.secret_getter(profile.id)
            if not secret:
                profile.last_error = "Secret belum disimpan."
                profile.health_status = "missing_secret"
                self.state_changed()
                continue
            try:
                result = operation(secret, profile)
                profile.last_error = ""
                profile.health_status = "healthy"
                self.state_changed()
                return result
            except Exception as error:
                last_error = error
                profile.last_error = str(error)
                if is_quota_error(error):
                    profile.cooldown_until = self.now() + retry_delay_seconds(error)
                    profile.health_status = "cooldown"
                    self.state_changed()
                    continue
                profile.health_status = "unhealthy"
                self.state_changed()
                raise
        if last_error:
            raise last_error
        raise RuntimeError("Semua Gemini API profile belum memiliki secret.")
