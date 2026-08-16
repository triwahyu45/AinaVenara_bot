from pathlib import Path

import pytest

from vroid_helper.core import (
    GuideItem,
    SafetyError,
    WindowInfo,
    contains_click,
    load_guides,
    record_guide,
    save_guides,
    validate_guide,
)


WINDOW = WindowInfo(10, "VRoid Studio", "vroidstudio.exe", 100, 200, 1000, 800)


def item(**overrides):
    values = {
        "id": "face-eye-color",
        "label": "Buka warna mata",
        "target": "vroid",
        "x": 0.5,
        "y": 0.25,
        "radius": 36,
        "capture_delay_ms": 700,
        "manual_review": True,
    }
    values.update(overrides)
    return GuideItem(**values)


def test_window_maps_relative_and_screen_coordinates():
    assert WINDOW.screen_point(0.5, 0.25) == (600, 400)
    assert WINDOW.relative_point(600, 400) == (0.5, 0.25)


def test_click_inside_highlight_matches_but_outside_does_not():
    guide = item()
    assert contains_click(guide, WINDOW, 600, 400) is True
    assert contains_click(guide, WINDOW, 700, 400) is False


def test_hover_hotkey_recording_uses_relative_coordinates():
    guide = record_guide(
        label="Buka warna mata",
        target="vroid",
        cursor_x=600,
        cursor_y=400,
        window=WINDOW,
        item_id="eye",
    )
    assert guide == item(id="eye")


def test_hover_recording_rejects_cursor_outside_window():
    with pytest.raises(SafetyError, match="0..1"):
        record_guide(label="Di luar", target="vroid", cursor_x=50, cursor_y=50, window=WINDOW)


def test_guides_round_trip_to_runtime_json(tmp_path):
    path = tmp_path / "guides.json"
    save_guides([item()], path)
    assert load_guides(path) == [item()]


def test_invalid_radius_delay_and_target_are_rejected():
    with pytest.raises(SafetyError, match="Radius"):
        validate_guide(item(radius=5))
    with pytest.raises(SafetyError, match="Delay"):
        validate_guide(item(capture_delay_ms=20))
    with pytest.raises(SafetyError, match="Target"):
        validate_guide(item(target="browser"))


def test_core_runtime_has_no_automatic_click_or_typing_surface():
    source = Path("vroid_helper/core.py").read_text(encoding="utf-8")
    assert "pyautogui" not in source
    assert ".click(" not in source
    assert ".typewrite(" not in source
    assert "clipboard" not in source
