from __future__ import annotations

import ctypes
import json
import os
import subprocess
from ctypes import wintypes
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime"
GUIDES_PATH = RUNTIME_DIR / "guides.json"
CHECKPOINT_DIR = RUNTIME_DIR / "checkpoints"
VROID_EXE = Path(r"C:\Program Files (x86)\Steam\steamapps\common\VRoid Studio\VRoidStudio.exe")
BLENDER_EXE = Path(r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe")


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str
    process_name: str
    left: int
    top: int
    width: int
    height: int

    @property
    def signature(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.width, self.height)

    def screen_point(self, x: float, y: float) -> tuple[int, int]:
        if not 0 <= x <= 1 or not 0 <= y <= 1:
            raise ValueError("Koordinat relatif harus berada di antara 0 dan 1.")
        return self.left + round(x * self.width), self.top + round(y * self.height)

    def relative_point(self, x: int, y: int) -> tuple[float, float]:
        return (x - self.left) / self.width, (y - self.top) / self.height


@dataclass
class GuideItem:
    id: str
    label: str
    target: str
    x: float
    y: float
    radius: int = 36
    capture_delay_ms: int = 700
    manual_review: bool = True


class SafetyError(RuntimeError):
    pass


def validate_guide(item: GuideItem) -> None:
    if item.target not in {"vroid", "blender"}:
        raise SafetyError(f"Target tidak didukung: {item.target}")
    if not 0 <= item.x <= 1 or not 0 <= item.y <= 1:
        raise SafetyError("Koordinat guide harus relatif terhadap window: 0..1.")
    if not 12 <= item.radius <= 160:
        raise SafetyError("Radius highlight harus berada di antara 12 dan 160 pixel.")
    if not 100 <= item.capture_delay_ms <= 5000:
        raise SafetyError("Delay capture harus berada di antara 100 dan 5000 ms.")
    if not item.label.strip():
        raise SafetyError("Label guide tidak boleh kosong.")


def contains_click(item: GuideItem, window: WindowInfo, click_x: int, click_y: int) -> bool:
    center_x, center_y = window.screen_point(item.x, item.y)
    return (click_x - center_x) ** 2 + (click_y - center_y) ** 2 <= item.radius**2


def record_guide(
    *,
    label: str,
    target: str,
    cursor_x: int,
    cursor_y: int,
    window: WindowInfo,
    item_id: str | None = None,
) -> GuideItem:
    x, y = window.relative_point(cursor_x, cursor_y)
    item = GuideItem(
        id=item_id or f"{target}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        label=label.strip(),
        target=target,
        x=round(x, 6),
        y=round(y, 6),
    )
    validate_guide(item)
    return item


def load_guides(path: Path = GUIDES_PATH) -> list[GuideItem]:
    if not path.exists():
        return []
    return [GuideItem(**value) for value in json.loads(path.read_text(encoding="utf-8"))]


def save_guides(items: list[GuideItem], path: Path = GUIDES_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    for item in items:
        validate_guide(item)
    path.write_text(json.dumps([asdict(item) for item in items], ensure_ascii=True, indent=2), encoding="utf-8")
    return path


class WindowLocator:
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

    def _process_name(self, hwnd: int) -> str:
        pid = ctypes.c_ulong()
        self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = self.kernel32.OpenProcess(self.PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not handle:
            return ""
        try:
            size = ctypes.c_ulong(4096)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not self.kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return ""
            return Path(buffer.value).name.lower()
        finally:
            self.kernel32.CloseHandle(handle)

    def list_windows(self) -> list[WindowInfo]:
        windows: list[WindowInfo] = []
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        @callback_type
        def callback(hwnd: int, _lparam: int) -> int:
            if not self.user32.IsWindowVisible(hwnd):
                return True
            length = self.user32.GetWindowTextLengthW(hwnd)
            if not length:
                return True
            title = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, title, length + 1)
            rect = wintypes.RECT()
            self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            width, height = rect.right - rect.left, rect.bottom - rect.top
            if width <= 0 or height <= 0:
                return True
            windows.append(
                WindowInfo(
                    hwnd=hwnd,
                    title=title.value,
                    process_name=self._process_name(hwnd),
                    left=rect.left,
                    top=rect.top,
                    width=width,
                    height=height,
                )
            )
            return True

        self.user32.EnumWindows(callback, 0)
        return windows

    def find(self, target: str) -> WindowInfo | None:
        expected = {"vroid": "vroidstudio.exe", "blender": "blender.exe"}[target]
        return next((window for window in self.list_windows() if window.process_name == expected), None)


class AuditLog:
    def __init__(self, path: Path | None = None):
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self.path = path or RUNTIME_DIR / "actions.jsonl"

    def write(self, event: str, **fields: Any) -> None:
        record = {
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "event": event,
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def capture_window(window: WindowInfo, destination: Path) -> Path:
    import mss

    destination.parent.mkdir(parents=True, exist_ok=True)
    with mss.mss() as capture:
        capture.shot(
            mon={"left": window.left, "top": window.top, "width": window.width, "height": window.height},
            output=str(destination),
        )
    return destination


def checkpoint_path(item: GuideItem, index: int) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return CHECKPOINT_DIR / f"{stamp}-{index + 1:02d}-{item.id}.png"


def launch_target(target: str) -> None:
    executable = {"vroid": VROID_EXE, "blender": BLENDER_EXE}[target]
    if not executable.exists():
        raise FileNotFoundError(f"Executable tidak ditemukan: {executable}")
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    subprocess.Popen([str(executable)], cwd=executable.parent, creationflags=creationflags)


def open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(path)

