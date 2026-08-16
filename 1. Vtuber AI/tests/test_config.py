from aina_companion.config import DEFAULT_SETTINGS, SettingsStore, deep_merge, migrate_settings


def test_deep_merge_preserves_defaults():
    merged = deep_merge(DEFAULT_SETTINGS, {"avatar": {"fps": 60}})
    assert merged["avatar"]["fps"] == 60
    assert merged["avatar"]["websocket_port"] == 8765
    assert merged["ui"]["advanced_mode"] is False
    assert merged["ui"]["start_with_windows"] is False
    assert merged["ui"]["desktop_shortcut"] is False


def test_settings_store_round_trip(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    settings = store.load()
    settings["character"]["name"] = "Aina Test"
    store.save(settings)
    assert store.load()["character"]["name"] == "Aina Test"


def test_migrate_settings_removes_vts_and_spout():
    settings = deep_merge(DEFAULT_SETTINGS, {"vts": {"auto_launch": True}, "overlay": {"fps": 60}})
    migrated = migrate_settings(settings)
    assert "vts" not in migrated
    assert "overlay" not in migrated
    assert migrated["avatar"]["fps"] == 30
