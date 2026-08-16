from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from aina_companion.config import SettingsStore
from aina_companion.memory import MemoryStore
from aina_companion.secrets import KeyringSecretStore, MemorySecretBackend
from aina_companion.ui import MainWindow, SettingsDialog


class FakeAvatarHub:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)

    def connected(self):
        return False

    def close(self):
        pass


class FakeLauncher:
    executable_path = ""

    def launch(self):
        return False

    def close(self):
        pass


class FakeListener:
    muted = False

    def stop(self):
        pass

    def listen_continuous(self, *_args):
        pass


class FakeGemini:
    pass


def make_window(tmp_path: Path) -> MainWindow:
    QApplication.instance() or QApplication([])
    store = SettingsStore(tmp_path / "settings.json")
    settings = store.load()
    settings["audio"]["muted"] = True
    settings["avatar"]["auto_launch"] = False
    store.save(settings)
    return MainWindow(
        store=store,
        secrets=KeyringSecretStore(MemorySecretBackend()),
        memory=MemoryStore(tmp_path / "memory.sqlite3"),
        avatar_hub=FakeAvatarHub(),
        avatar_launcher=FakeLauncher(),
        listener=FakeListener(),
        gemini_factory=lambda _settings, _profiles: FakeGemini(),
        start_runtime=False,
    )


def test_compact_chat_send_button_and_enter_emit_message(tmp_path, monkeypatch):
    ui = make_window(tmp_path)
    sent = []
    monkeypatch.setattr(ui, "send_message", sent.append)

    ui.input.setText("dari tombol")
    ui.findChild(QPushButton, "sendButton").click()
    ui.input.setText("dari enter")
    ui.input.returnPressed.emit()

    assert sent == ["dari tombol", "dari enter"]
    ui.shutdown()


def test_settings_gear_opens_dialog(tmp_path, monkeypatch):
    ui = make_window(tmp_path)
    opened = []
    monkeypatch.setattr(SettingsDialog, "exec", lambda _dialog: opened.append(True))

    ui.findChild(QPushButton, "settingsButton").click()

    assert opened == [True]
    ui.shutdown()


def test_mic_toggle_updates_color_tooltip_and_listener_state(tmp_path):
    ui = make_window(tmp_path)
    assert ui.mute.toolTip() == "Microphone mute"
    assert "#EF4444" in ui.mute.styleSheet()

    ui.mute.click()

    assert ui.listener.muted is False
    assert ui.mute.toolTip() == "Microphone aktif"
    assert "#22C55E" in ui.mute.styleSheet()
    ui.shutdown()


def test_settings_memory_editor_accepts_uuid_fact_id(tmp_path):
    ui = make_window(tmp_path)
    fact_id = ui.memory.add_fact("User suka kopi.")
    ui.settings["ui"]["advanced_mode"] = True
    dialog = SettingsDialog(ui)
    dialog.facts.setCurrentRow(0)

    assert dialog._selected_fact_id() == fact_id
    dialog.close()
    ui.shutdown()


def test_append_chat_escapes_html(tmp_path):
    ui = make_window(tmp_path)
    ui.append_chat("<script>", "<b>raw</b>")

    assert "<script>" not in ui.chat.toHtml()
    assert "<b>raw</b>" in ui.chat.toPlainText()
    ui.shutdown()
