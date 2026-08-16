from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "Build", "Library", "Temp", "Logs"}
FORBIDDEN_NAMES = {
    "api_keys.env",
    "vtuber_token.txt",
    "settings.json",
    "memory.sqlite3",
    "memory_v2.sqlite3",
}
PATTERNS = {
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "Groq API key": re.compile(r"gsk_[0-9A-Za-z_-]{20,}"),
    "ElevenLabs API key": re.compile(r"sk_[0-9A-Za-z_-]{20,}"),
    "Service account private key": re.compile(r"-----BEGIN PRIVATE " r"KEY-----"),
}


def files():
    for path in ROOT.rglob("*"):
        if path.is_dir() or any(part in IGNORED_DIRS for part in path.parts):
            continue
        yield path


def main() -> int:
    findings: list[str] = []
    for path in files():
        relative = path.relative_to(ROOT)
        if (
            path.name in FORBIDDEN_NAMES
            or path.name == ".env"
            or "service-account" in path.name.lower()
            or "cloud-stt" in path.name.lower()
        ):
            findings.append(f"Forbidden local file: {relative}")
            continue
        if path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{label}: {relative}")
    if findings:
        print("\n".join(findings))
        return 1
    print("Secret scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
