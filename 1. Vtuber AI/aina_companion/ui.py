from __future__ import annotations

import threading
from html import escape
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .audio import AudioPlayer, SpeechListener
from .avatar import (
    SEED_SAN_LICENSE,
    AvatarHub,
    UnityAvatarLauncher,
    avatar_event,
    download_seed_san,
)
from .config import SettingsStore
from .diagnostics import dependency_report
from .gemini import GeminiService
from .memory import MemoryStore
from .orchestrator import ConversationOrchestrator
from .profiles import ApiProfile, ApiProfileManager
from .secrets import KeyringSecretStore
from .startup import set_desktop_shortcut, set_start_with_windows


class Bridge(QObject):
    message = Signal(str, str)
    status = Signal(str)
    completed = Signal(object, object)


class SettingsDialog(QDialog):
    def __init__(self, parent: "MainWindow"):
        super().__init__(parent)
        self.parent = parent
        self.settings = parent.settings
        self.setWindowTitle("Aina Settings")
        self.resize(680, 500)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._general_tab(), "General")
        self.tabs.addTab(self._audio_tab(), "Audio")
        self.tabs.addTab(self._avatar_tab(), "Avatar")
        self._apply_advanced_tabs()
        save = QPushButton("Simpan Settings")
        save.clicked.connect(self._save)
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addWidget(save)

    def _form_tab(self) -> tuple[QWidget, QFormLayout]:
        tab = QWidget()
        return tab, QFormLayout(tab)

    def _general_tab(self) -> QWidget:
        tab, form = self._form_tab()
        self.name = QLineEdit(self.settings["character"]["name"])
        self.persona = QTextEdit(self.settings["character"]["persona"])
        self.advanced = QCheckBox("Tampilkan advanced settings")
        self.advanced.setChecked(self.settings["ui"]["advanced_mode"])
        self.advanced.toggled.connect(lambda _value: self._apply_advanced_tabs())
        self.startup = QCheckBox("Jalankan Aina otomatis saat login Windows")
        self.startup.setChecked(self.settings["ui"]["start_with_windows"])
        self.desktop_shortcut = QCheckBox("Buat shortcut Aina di Desktop")
        self.desktop_shortcut.setChecked(self.settings["ui"]["desktop_shortcut"])
        form.addRow("Nama karakter", self.name)
        form.addRow("Persona", self.persona)
        form.addRow(self.startup)
        form.addRow(self.desktop_shortcut)
        form.addRow(self.advanced)
        return tab

    def _apply_advanced_tabs(self) -> None:
        while self.tabs.count() > 3:
            self.tabs.removeTab(3)
        if getattr(self, "advanced", None) and self.advanced.isChecked():
            self.tabs.addTab(self._api_tab(), "Gemini API")
            self.tabs.addTab(self._avatar_advanced_tab(), "Avatar Advanced")
            self.tabs.addTab(self._memory_tab(), "Memory")
            self.tabs.addTab(self._diagnostics_tab(), "Diagnostics")

    def _api_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.api_mode = QComboBox()
        self.api_mode.addItems(["auto", "specific"])
        self.api_mode.setCurrentText(self.settings["gemini"]["mode"])
        self.profile_list = QListWidget()
        self._refresh_profiles()
        self.profile_label = QLineEdit()
        self.profile_secret = QLineEdit()
        self.profile_secret.setEchoMode(QLineEdit.Password)
        add = QPushButton("Tambah / perbarui profile")
        add.clicked.connect(self._add_profile)
        delete = QPushButton("Hapus profile terpilih")
        delete.clicked.connect(self._delete_profile)
        test = QPushButton("Test profile terpilih")
        test.clicked.connect(self._test_profile)
        migrate = QPushButton("Impor key dari .env lokal")
        migrate.clicked.connect(self._import_env)
        layout.addWidget(QLabel("Mode pemilihan API"))
        layout.addWidget(self.api_mode)
        layout.addWidget(self.profile_list)
        layout.addWidget(QLabel("Label profile"))
        layout.addWidget(self.profile_label)
        layout.addWidget(QLabel("API key baru"))
        layout.addWidget(self.profile_secret)
        for button in (add, delete, test, migrate):
            layout.addWidget(button)
        return tab

    def _audio_tab(self) -> QWidget:
        tab, form = self._form_tab()
        self.mic_mode = QComboBox()
        self.mic_mode.addItems(["continuous", "push_to_talk"])
        self.mic_mode.setCurrentText(self.settings["audio"]["mic_mode"])
        self.cloud_stt_credentials = QLineEdit(self.settings["audio"]["cloud_stt_credentials_path"])
        test_speaker = QPushButton("Test speaker dengan suara Aina")
        test_speaker.clicked.connect(lambda: self.parent.run_tts_preview("Halo, ini tes suara Aina."))
        form.addRow("Mode microphone", self.mic_mode)
        form.addRow("Google Cloud STT credential JSON", self.cloud_stt_credentials)
        form.addRow(test_speaker)
        return tab

    def _avatar_tab(self) -> QWidget:
        tab, form = self._form_tab()
        avatar = self.settings["avatar"]
        self.avatar_launch = QCheckBox("Jalankan renderer Unity otomatis")
        self.avatar_launch.setChecked(avatar["auto_launch"])
        self.avatar_bubble = QCheckBox("Tampilkan bubble subtitle")
        self.avatar_bubble.setChecked(avatar["bubble"])
        self.avatar_click = QCheckBox("Click-through")
        self.avatar_click.setChecked(avatar["click_through"])
        self.avatar_top = QCheckBox("Always on top")
        self.avatar_top.setChecked(avatar["always_on_top"])
        self.avatar_fps = QComboBox()
        self.avatar_fps.addItems(["30", "60"])
        self.avatar_fps.setCurrentText(str(avatar["fps"]))
        form.addRow(self.avatar_launch)
        form.addRow(self.avatar_bubble)
        form.addRow(self.avatar_click)
        form.addRow(self.avatar_top)
        form.addRow("Target FPS", self.avatar_fps)
        return tab

    def _avatar_advanced_tab(self) -> QWidget:
        tab, form = self._form_tab()
        avatar = self.settings["avatar"]
        self.avatar_executable = QLineEdit(avatar["executable_path"])
        self.avatar_model = QLineEdit(avatar["model_path"])
        choose_model = QPushButton("Pilih file VRM")
        choose_model.clicked.connect(self._choose_model)
        choose_animation = QPushButton("Pilih dan mainkan template VRMA")
        choose_animation.clicked.connect(self._choose_animation)
        launch = QPushButton("Launch Unity Renderer")
        launch.clicked.connect(lambda: self.parent.set_status(
            "Unity renderer dijalankan." if self.parent.avatar_launcher.launch()
            else "Renderer belum dibuild. Jalankan scripts\\build_unity_renderer.cmd."
        ))
        demo = QPushButton("Download model demo Seed-san")
        demo.clicked.connect(self._download_demo)
        test = QPushButton("Test animasi marah")
        test.clicked.connect(lambda: self.parent.test_avatar_animation("marah"))
        form.addRow("Renderer .exe", self.avatar_executable)
        form.addRow("Model .vrm", self.avatar_model)
        form.addRow(choose_model)
        form.addRow(choose_animation)
        form.addRow(launch)
        form.addRow(demo)
        form.addRow(test)
        return tab

    def _memory_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.facts = QListWidget()
        for fact in self.parent.memory.facts():
            self.facts.addItem(f"{fact['id']}: {fact['content']}")
        self.fact_input = QLineEdit()
        add = QPushButton("Tambah fakta")
        add.clicked.connect(self._add_fact)
        update = QPushButton("Perbarui fakta terpilih")
        update.clicked.connect(self._update_fact)
        delete = QPushButton("Hapus fakta terpilih")
        delete.clicked.connect(self._delete_fact)
        self.sessions = QListWidget()
        self._refresh_sessions()
        new_session = QPushButton("Percakapan baru")
        new_session.clicked.connect(self._new_session)
        open_session = QPushButton("Buka percakapan terpilih")
        open_session.clicked.connect(self._open_session)
        clear = QPushButton("Hapus seluruh memory lokal")
        clear.clicked.connect(self._clear_memory)
        layout.addWidget(QLabel("Fakta penting yang dapat diedit dari database lokal"))
        layout.addWidget(self.facts)
        layout.addWidget(self.fact_input)
        layout.addWidget(add)
        layout.addWidget(update)
        layout.addWidget(delete)
        layout.addWidget(QLabel("Sesi percakapan lokal"))
        layout.addWidget(self.sessions)
        layout.addWidget(new_session)
        layout.addWidget(open_session)
        layout.addWidget(clear)
        return tab

    def _diagnostics_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        output = QTextEdit()
        output.setReadOnly(True)
        output.setPlainText("\n".join(dependency_report()))
        refresh = QPushButton("Refresh dependency status")
        refresh.clicked.connect(lambda: output.setPlainText("\n".join(dependency_report())))
        test_chat = QPushButton("Test chat Gemini")
        test_chat.clicked.connect(lambda: self.parent.send_message("Balas singkat: koneksi chat berhasil."))
        test_tts = QPushButton("Preview Gemini TTS")
        test_tts.clicked.connect(lambda: self.parent.run_tts_preview("Tes suara Aina berhasil."))
        test_mic = QPushButton("Test microphone sekali")
        test_mic.clicked.connect(self.parent.push_to_talk)
        test_avatar = QPushButton("Test Unity avatar connection")
        test_avatar.clicked.connect(self.parent.test_avatar_connection)
        test_emotion = QPushButton("Test avatar senyum")
        test_emotion.clicked.connect(lambda: self.parent.test_avatar_animation("senyum"))
        layout.addWidget(output)
        for button in (refresh, test_chat, test_tts, test_mic, test_avatar, test_emotion):
            layout.addWidget(button)
        return tab

    def _choose_model(self) -> None:
        selected, _filter = QFileDialog.getOpenFileName(self, "Pilih model VRM", "", "VRM Model (*.vrm)")
        if selected:
            self.avatar_model.setText(selected)

    def _download_demo(self) -> None:
        accepted = QMessageBox.question(
            self,
            "Lisensi Seed-san",
            "Model demo Seed-san akan diunduh lokal dan tidak masuk Git.\n"
            f"Lisensi: {SEED_SAN_LICENSE}\n\nLanjutkan download?",
        )
        if accepted != QMessageBox.Yes:
            return
        self.parent.run_background(
            download_seed_san,
            lambda path: self.avatar_model.setText(str(path)),
        )

    def _choose_animation(self) -> None:
        selected, _filter = QFileDialog.getOpenFileName(self, "Pilih template animasi", "", "VRM Animation (*.vrma)")
        if selected:
            self.parent.avatar_hub.send(avatar_event("animation.play", path=selected))

    def _refresh_profiles(self) -> None:
        self.profile_list.clear()
        for profile in self.parent.profiles:
            self.profile_list.addItem(f"{profile.label} [{profile.id[:8]}]")

    def _selected_profile(self) -> ApiProfile | None:
        row = self.profile_list.currentRow()
        return self.parent.profiles[row] if 0 <= row < len(self.parent.profiles) else None

    def _add_profile(self) -> None:
        label = self.profile_label.text().strip()
        secret = self.profile_secret.text().strip()
        if not label or not secret:
            QMessageBox.warning(self, "API profile", "Isi label dan API key.")
            return
        profile = ApiProfile.create(label)
        self.parent.profiles.append(profile)
        self.parent.secrets.set(profile.id, secret)
        self.profile_secret.clear()
        self._refresh_profiles()

    def _delete_profile(self) -> None:
        profile = self._selected_profile()
        if profile:
            self.parent.secrets.delete(profile.id)
            self.parent.profiles.remove(profile)
            self._refresh_profiles()

    def _test_profile(self) -> None:
        profile = self._selected_profile()
        if not profile:
            return
        secret = self.parent.secrets.get(profile.id)
        self.parent.run_background(
            lambda: self.parent.gemini.test_key(secret or ""),
            lambda result: QMessageBox.information(self, "Gemini API", f"Berhasil: {result}"),
        )

    def _import_env(self) -> None:
        candidates = [Path(".env"), Path("api_keys.env")]
        imported = []
        for candidate in candidates:
            imported.extend(self.parent.secrets.import_env(candidate))
        for label, secret in imported:
            profile = ApiProfile.create(label)
            self.parent.profiles.append(profile)
            self.parent.secrets.set(profile.id, secret)
        self._refresh_profiles()
        QMessageBox.information(self, "Migrasi", f"{len(imported)} key diimpor ke Credential Manager.")

    def _add_fact(self) -> None:
        self.parent.memory.add_fact(self.fact_input.text())
        self.fact_input.clear()
        self._refresh_facts()

    def _refresh_facts(self) -> None:
        self.facts.clear()
        for fact in self.parent.memory.facts():
            self.facts.addItem(f"{fact['id']}: {fact['content']}")

    def _selected_fact_id(self) -> str | None:
        item = self.facts.currentItem()
        return item.text().split(":", 1)[0] if item else None

    def _update_fact(self) -> None:
        fact_id = self._selected_fact_id()
        if fact_id and self.fact_input.text().strip():
            self.parent.memory.update_fact(fact_id, self.fact_input.text())
            self.fact_input.clear()
            self._refresh_facts()

    def _delete_fact(self) -> None:
        fact_id = self._selected_fact_id()
        if fact_id:
            self.parent.memory.delete_fact(fact_id)
            self._refresh_facts()

    def _refresh_sessions(self) -> None:
        self.sessions.clear()
        for session in self.parent.memory.sessions():
            self.sessions.addItem(f"{session['id']}: {session['title']} ({session['updated_at']})")

    def _new_session(self) -> None:
        self.parent.session_id = self.parent.memory.create_session()
        self._refresh_sessions()

    def _open_session(self) -> None:
        item = self.sessions.currentItem()
        if item:
            self.parent.session_id = item.text().split(":", 1)[0]

    def _clear_memory(self) -> None:
        self.parent.memory.clear()
        self.parent.session_id = self.parent.memory.ensure_session()
        self.facts.clear()

    def _save(self) -> None:
        self.settings["character"]["name"] = self.name.text()
        self.settings["character"]["persona"] = self.persona.toPlainText()
        self.settings["ui"]["advanced_mode"] = self.advanced.isChecked()
        self.settings["ui"]["start_with_windows"] = self.startup.isChecked()
        self.settings["ui"]["desktop_shortcut"] = self.desktop_shortcut.isChecked()
        if hasattr(self, "api_mode"):
            self.settings["gemini"]["mode"] = self.api_mode.currentText()
            selected = self._selected_profile()
            self.settings["gemini"]["specific_profile_id"] = selected.id if selected else ""
            self.settings["gemini"]["profiles"] = [profile.to_dict() for profile in self.parent.profiles]
        self.settings["audio"]["mic_mode"] = self.mic_mode.currentText()
        self.settings["audio"]["cloud_stt_credentials_path"] = self.cloud_stt_credentials.text().strip()
        if hasattr(self, "avatar_executable"):
            self.settings["avatar"]["executable_path"] = self.avatar_executable.text()
            self.settings["avatar"]["model_path"] = self.avatar_model.text()
        self.settings["avatar"]["auto_launch"] = self.avatar_launch.isChecked()
        self.settings["avatar"]["bubble"] = self.avatar_bubble.isChecked()
        self.settings["avatar"]["click_through"] = self.avatar_click.isChecked()
        self.settings["avatar"]["always_on_top"] = self.avatar_top.isChecked()
        self.settings["avatar"]["fps"] = int(self.avatar_fps.currentText())
        self.parent.store.save(self.settings)
        set_start_with_windows(self.settings["ui"]["start_with_windows"])
        set_desktop_shortcut(self.settings["ui"]["desktop_shortcut"])
        self.parent.rebuild_services()
        self.accept()


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        store: SettingsStore | None = None,
        secrets: Any | None = None,
        memory: MemoryStore | None = None,
        avatar_hub: Any | None = None,
        avatar_launcher: Any | None = None,
        listener: Any | None = None,
        gemini_factory: Callable[[dict[str, Any], ApiProfileManager], Any] = GeminiService,
        start_runtime: bool = True,
    ):
        super().__init__()
        self.store = store or SettingsStore()
        self.settings = self.store.load()
        self.secrets = secrets or KeyringSecretStore()
        self.memory = memory or MemoryStore()
        self.session_id = self.memory.ensure_session()
        self.bridge = Bridge()
        self.bridge.message.connect(self.append_chat)
        self.bridge.status.connect(self.set_status)
        self.bridge.completed.connect(lambda callback, result: callback(result))
        avatar = self.settings["avatar"]
        self.avatar_hub = avatar_hub or AvatarHub(avatar["websocket_host"], avatar["websocket_port"])
        self.avatar_launcher = avatar_launcher or UnityAvatarLauncher(avatar["executable_path"])
        self.audio_player = None
        self.listener = listener or SpeechListener(
            self._mic_text,
            lambda text: self.bridge.status.emit(text),
            self.settings["audio"]["cloud_stt_credentials_path"],
        )
        self.gemini_factory = gemini_factory
        self.rebuild_services()
        self._build_ui()
        self._build_tray()
        if start_runtime and self.mute.isChecked():
            self.toggle_mic()
        if start_runtime and avatar["auto_launch"]:
            self.avatar_launcher.launch()
        self.send_avatar_config()

    def rebuild_services(self) -> None:
        self.profiles = [ApiProfile.from_dict(item) for item in self.settings["gemini"]["profiles"]]
        self.profile_manager = ApiProfileManager(
            self.profiles,
            self.secrets.get,
            self.settings["gemini"]["mode"],
            self.settings["gemini"]["specific_profile_id"],
            state_changed=self.persist_profile_state,
        )
        self.gemini = self.gemini_factory(self.settings, self.profile_manager)
        if hasattr(self, "listener"):
            self.listener.credentials_path = self.settings["audio"]["cloud_stt_credentials_path"]
        if hasattr(self, "avatar_hub"):
            self.orchestrator = ConversationOrchestrator(
                memory=self.memory,
                gemini=self.gemini,
                avatar_hub=self.avatar_hub,
                settings=self.settings,
                session_id=self.session_id,
            )
        if hasattr(self, "avatar_launcher"):
            self.avatar_launcher.executable_path = self.settings["avatar"]["executable_path"]
            self.send_avatar_config()

    def persist_profile_state(self) -> None:
        self.settings["gemini"]["profiles"] = [profile.to_dict() for profile in self.profiles]
        self.store.save(self.settings)

    def _build_ui(self) -> None:
        self.setWindowTitle("Aina Desktop Companion")
        self.resize(430, 480)
        central = QWidget()
        layout = QVBoxLayout(central)
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setObjectName("chat")
        self.status = QLabel("Siap.")
        self.status.setObjectName("status")
        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Tulis pesan untuk Aina...")
        self.input.returnPressed.connect(self._send_input)
        send = QPushButton("➤")
        send.setText("\u27a4")
        send.setToolTip("Kirim pesan")
        send.setObjectName("sendButton")
        send.clicked.connect(self._send_input)
        row.addWidget(self.input)
        row.addWidget(send)
        controls = QHBoxLayout()
        self.mute = QPushButton("🎙")
        self.mute.setText("\U0001f399")
        self.mute.setObjectName("micButton")
        self.mute.setCheckable(True)
        self.mute.setChecked(not self.settings["audio"]["muted"])
        self.mute.clicked.connect(self.toggle_mic)
        settings = QPushButton("⚙")
        settings.setText("\u2699")
        settings.setToolTip("Settings")
        settings.setObjectName("settingsButton")
        settings.clicked.connect(self.open_settings)
        controls.addWidget(self.mute)
        controls.addStretch()
        controls.addWidget(settings)
        layout.addWidget(self.chat)
        layout.addLayout(row)
        layout.addLayout(controls)
        layout.addWidget(self.status)
        self.setCentralWidget(central)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #111318; color: #E5E7EB; font-family: Segoe UI; }
            QTextEdit#chat { background: #181B22; border: 1px solid #252A34; border-radius: 14px; padding: 8px; }
            QLineEdit { background: #181B22; border: 1px solid #303644; border-radius: 16px; padding: 8px 12px; }
            QPushButton { background: #252A34; border: none; border-radius: 14px; padding: 7px 12px; }
            QPushButton:hover { background: #353C4A; }
            QPushButton#sendButton, QPushButton#settingsButton, QPushButton#micButton { min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; font-size: 18px; }
            QLabel#status { color: #94A3B8; font-size: 11px; padding-left: 4px; }
        """)
        self._refresh_mic_style()

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(self._tray_icon(), self)
        menu = QMenu()
        for text, callback in (
            ("Show / hide chat", self.toggle_chat),
            ("Show / hide avatar", self.toggle_avatar),
            ("Toggle click-through", self.toggle_click_through),
            ("Mute / unmute mic", lambda: self.mute.click()),
            ("Settings", self.open_settings),
            ("Keluar", QApplication.quit),
        ):
            action = QAction(text, self)
            action.triggered.connect(callback)
            menu.addAction(action)
        self.tray.setContextMenu(menu)
        self.tray.show()

    @staticmethod
    def _tray_icon() -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#EC4899"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.setPen(QColor("white"))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(38)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "A")
        painter.end()
        return QIcon(pixmap)

    def run_background(self, operation: Callable, on_success: Callable | None = None) -> None:
        def worker():
            try:
                result = operation()
                if on_success:
                    self.bridge.completed.emit(on_success, result)
            except Exception as error:
                self.bridge.status.emit(str(error))

        threading.Thread(target=worker, daemon=True).start()

    def open_settings(self) -> None:
        SettingsDialog(self).exec()

    def _send_input(self) -> None:
        text = self.input.text().strip()
        if text:
            self.input.clear()
            self.send_message(text)

    def send_message(self, text: str) -> None:
        self.append_chat("Kamu", text)
        self.set_status("Aina sedang berpikir...")
        self.avatar_hub.send(avatar_event("state", value="thinking"))

        def operation():
            self.orchestrator.session_id = self.session_id
            return self.orchestrator.process_text(text).reply

        def done(reply):
            self.bridge.message.emit(f"Aina [{reply.emotion}]", reply.text)
            self.bridge.status.emit("Siap.")
            self.run_tts_preview(reply.text, reply.emotion)

        self.run_background(operation, done)

    def append_chat(self, sender: str, text: str) -> None:
        self.chat.append(f"<b>{escape(sender)}</b><br>{escape(text)}<br>")

    def set_status(self, text: str) -> None:
        self.status.setText(text)

    def run_tts_preview(self, text: str, emotion: str = "biasa") -> None:
        def operation():
            if self.audio_player is None:
                self.audio_player = AudioPlayer()
            return self.orchestrator.speak(text, emotion, self.audio_player)

        self.run_background(operation)

    def toggle_mic(self) -> None:
        enabled = self.mute.isChecked()
        self.listener.muted = not enabled
        self.settings["audio"]["muted"] = not enabled
        self.store.save(self.settings)
        self._refresh_mic_style()
        if enabled and self.settings["audio"]["mic_mode"] == "continuous":
            self.run_background(lambda: self.listener.listen_continuous(
                self.settings["audio"]["stt_language"],
                self.settings["audio"]["microphone_index"],
            ))
        elif not enabled:
            self.listener.stop()

    def _refresh_mic_style(self) -> None:
        enabled = self.mute.isChecked()
        color = "#22C55E" if enabled else "#EF4444"
        self.mute.setStyleSheet(f"color: {color}; background: #252A34; border-radius: 16px;")
        self.mute.setToolTip("Microphone aktif" if enabled else "Microphone mute")

    def push_to_talk(self) -> None:
        self.run_background(
            lambda: self.listener.listen_once(
                self.settings["audio"]["stt_language"],
                self.settings["audio"]["microphone_index"],
            ),
            self.send_message,
        )

    def _mic_text(self, text: str) -> None:
        self.bridge.status.emit(f"Terdengar: {text}")
        self.send_message(text)

    def test_avatar_connection(self) -> None:
        self.set_status(
            "Unity renderer terhubung." if self.avatar_hub.connected()
            else "Unity renderer belum terhubung. Build lalu launch renderer."
        )

    def test_avatar_animation(self, emotion: str) -> None:
        self.avatar_hub.send(avatar_event("emotion", value=emotion, intensity=1.0, duration_ms=3500))
        self.set_status(f"Event animasi {emotion} dikirim.")

    def send_avatar_config(self) -> None:
        avatar = self.settings["avatar"]
        self.avatar_hub.send(avatar_event(
            "config",
            bubble=avatar["bubble"],
            click_through=avatar["click_through"],
            always_on_top=avatar["always_on_top"],
            fps=avatar["fps"],
            visible=avatar["visible"],
        ))
        if avatar["model_path"]:
            self.avatar_hub.send(avatar_event("model.load", path=avatar["model_path"]))

    def toggle_click_through(self) -> None:
        self.settings["avatar"]["click_through"] = not self.settings["avatar"]["click_through"]
        self.store.save(self.settings)
        self.send_avatar_config()

    def toggle_avatar(self) -> None:
        self.settings["avatar"]["visible"] = not self.settings["avatar"]["visible"]
        self.store.save(self.settings)
        if self.settings["avatar"]["visible"]:
            self.avatar_launcher.launch()
        self.send_avatar_config()

    def toggle_chat(self) -> None:
        self.hide() if self.isVisible() else self.show()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
        self.tray.showMessage("Aina", "Aina tetap berjalan di system tray.")

    def shutdown(self) -> None:
        self.listener.stop()
        self.memory.close()
        self.avatar_hub.close()
        self.avatar_launcher.close()
