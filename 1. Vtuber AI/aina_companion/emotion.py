from __future__ import annotations

import re

EMOTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*(.*)$", re.S)


def parse_emotion(text: str, valid_emotions: set[str]) -> tuple[str, str]:
    match = EMOTION_RE.match(text.strip())
    if not match:
        return "biasa", text.strip()
    emotion = match.group(1).strip().lower()
    if emotion not in valid_emotions:
        emotion = "biasa"
    return emotion, match.group(2).strip()


def emotion_prompt(emotions: dict[str, str | None]) -> str:
    tags = ", ".join(f"[{name.capitalize()}]" for name in emotions)
    return f"Gunakan tepat satu tag emosi di awal jawaban: {tags}."

