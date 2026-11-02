# Version: 0.2.0 | 2026-11-02
from dataclasses import replace
import json

import pytest
from cradle.platform.config import Config, load_config, resolve_paths, save_config


def test_paths_precedence(cradle_home, monkeypatch):
    # Spec §4 / WP-1.1: explicit CRADLE_HOME wins over OS locations.
    paths = resolve_paths()
    assert paths.home == cradle_home
    assert paths.config == cradle_home / "config.json"
    assert paths.saves == cradle_home / "saves"
    assert paths.backups == cradle_home / "backups"
    assert paths.logs == cradle_home / "logs"
    assert not paths.saves.exists()  # path resolution is read-only


@pytest.mark.parametrize(
    "platform,env,suffix",
    [
        ("win32", {"LOCALAPPDATA": "/tmp/local"}, "/tmp/local/Cradle"),
        (
            "darwin",
            {"HOME": "/tmp/user"},
            "/tmp/user/Library/Application Support/Cradle",
        ),
        (
            "linux",
            {"XDG_DATA_HOME": "/tmp/data", "HOME": "/tmp/user"},
            "/tmp/data/cradle",
        ),
        ("linux", {"HOME": "/tmp/user"}, "/tmp/user/.local/share/cradle"),
    ],
)
def test_os_paths(platform, env, suffix, monkeypatch):
    # Spec §4: stdlib-only cross-platform path decisions.
    monkeypatch.setattr("cradle.platform.config.sys.platform", platform)
    assert str(resolve_paths(env).home) == suffix


def test_no_user_directory_falls_back(tmp_path, monkeypatch):
    # Spec §4 fallback.
    monkeypatch.chdir(tmp_path)
    assert resolve_paths({}).home == tmp_path / "userdata"


@pytest.mark.parametrize(
    "contents",
    [
        "{",
        "[]",
        "null",
        "42",
        "{}",
        '{"window_scale": true, "time_lag": 10, "sound": 1, "debug": "true"}',
    ],
)
def test_config_default_recovery(contents, tmp_path):
    # Spec §4 / §11: malformed config does not prevent startup.
    path = tmp_path / "config.json"
    path.write_text(contents, encoding="utf-8", newline="\n")
    assert load_config(path, {}) == Config()


def test_config_roundtrip_and_debug_override(tmp_path):
    # D-2 / spec §4: sound persists; CRADLE_DEBUG=1 overrides.
    path = tmp_path / "settings" / "config.json"
    cfg = load_config(path, {})
    save_config(replace(cfg, window_scale=3, time_lag=0, sound=False))
    loaded = load_config(path, {"CRADLE_DEBUG": "1"})
    assert (loaded.window_scale, loaded.time_lag, loaded.sound, loaded.debug) == (
        3,
        0,
        False,
        True,
    )
    assert json.loads(path.read_text(encoding="utf-8"))["sound"] is False
    assert not path.with_suffix(".json.tmp").exists()


def test_config_rejects_bad_write(tmp_path):
    # Spec §4: invalid writes cannot replace existing config.
    cfg = load_config(tmp_path / "config.json", {})
    save_config(cfg)
    before = cfg.path.read_bytes()
    with pytest.raises(ValueError):
        save_config(replace(cfg, window_scale=0))
    assert cfg.path.read_bytes() == before
