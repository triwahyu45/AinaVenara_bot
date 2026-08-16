from pathlib import Path

from aina_companion import startup
from aina_companion.startup import launcher_script


def test_launcher_uses_pythonw_without_console(tmp_path):
    script = launcher_script(tmp_path)
    assert "pythonw.exe" in script
    assert "-m aina_companion" in script
    assert ', 0, False' in script
    assert 'shell.Run """' in script


def test_startup_shortcut_can_be_created_and_removed(tmp_path, monkeypatch):
    target = tmp_path / "Startup" / "Aina.vbs"
    monkeypatch.setattr(startup, "startup_shortcut_path", lambda: target)
    assert startup.set_start_with_windows(True) == target
    assert target.exists()
    startup.set_start_with_windows(False)
    assert not target.exists()


def test_desktop_shortcut_can_be_created_and_removed(tmp_path, monkeypatch):
    target = tmp_path / "Desktop" / "Aina.vbs"
    monkeypatch.setattr(startup, "desktop_shortcut_path", lambda: target)
    assert startup.set_desktop_shortcut(True) == target
    assert target.exists()
    startup.set_desktop_shortcut(False)
    assert not target.exists()
