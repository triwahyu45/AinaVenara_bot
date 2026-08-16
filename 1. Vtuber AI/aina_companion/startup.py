from __future__ import annotations

import os
from pathlib import Path

SHORTCUT_NAME = "Aina Desktop Companion.vbs"


def project_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def startup_dir() -> Path:
    appdata = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    return appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def launcher_path() -> Path:
    return project_dir() / "Launch Aina.vbs"


def startup_shortcut_path() -> Path:
    return startup_dir() / SHORTCUT_NAME


def desktop_shortcut_path() -> Path:
    return Path.home() / "Desktop" / SHORTCUT_NAME


def launcher_script(root: Path | None = None) -> str:
    target = root or project_dir()
    pythonw = target / ".venv" / "Scripts" / "pythonw.exe"
    return "\n".join(
        [
            'Set shell = CreateObject("WScript.Shell")',
            f'shell.CurrentDirectory = "{target}"',
            f'shell.Run """{pythonw}"" -m aina_companion", 0, False',
            "",
        ]
    )


def ensure_launcher() -> Path:
    target = launcher_path()
    target.write_text(launcher_script(), encoding="utf-8")
    return target


def set_start_with_windows(enabled: bool) -> Path:
    shortcut = startup_shortcut_path()
    if enabled:
        shortcut.parent.mkdir(parents=True, exist_ok=True)
        shortcut.write_text(launcher_script(), encoding="utf-8")
    elif shortcut.exists():
        shortcut.unlink()
    return shortcut


def set_desktop_shortcut(enabled: bool) -> Path:
    shortcut = desktop_shortcut_path()
    if enabled:
        shortcut.parent.mkdir(parents=True, exist_ok=True)
        shortcut.write_text(launcher_script(), encoding="utf-8")
    elif shortcut.exists():
        shortcut.unlink()
    return shortcut
