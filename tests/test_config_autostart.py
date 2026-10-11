import config


def test_shared_config_defaults_include_autostart_migrated(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "SHARED_CONFIG_FILE", str(tmp_path / "config_shared.json"))

    shared = config.load_shared_config()

    assert shared["autostart_migrated"] is False


def test_mark_autostart_migrated_persists(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "SHARED_CONFIG_FILE", str(tmp_path / "config_shared.json"))

    config.mark_autostart_migrated()

    assert config.load_shared_config()["autostart_migrated"] is True


def test_mark_autostart_migrated_preserves_other_keys(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "SHARED_CONFIG_FILE", str(tmp_path / "config_shared.json"))
    config.add_to_whitelist("chrome.exe")

    config.mark_autostart_migrated()

    shared = config.load_shared_config()
    assert shared["autostart_migrated"] is True
    assert shared["whitelist"] == ["chrome.exe"]
