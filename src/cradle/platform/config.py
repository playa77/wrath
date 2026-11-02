# Version: 0.2.0 | 2026-11-02
"""Spec §4: local configuration and stdlib-only path resolution."""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Mapping
import sys


@dataclass(frozen=True)
class Paths:
    home: Path
    content: Path

    @property
    def config(self) -> Path:
        return self.home / "config.json"

    @property
    def saves(self) -> Path:
        return self.home / "saves"

    @property
    def backups(self) -> Path:
        return self.home / "backups"

    @property
    def logs(self) -> Path:
        return self.home / "logs"


@dataclass(frozen=True)
class Config:
    window_scale: int = 1
    time_lag: int = 4
    sound: bool = True
    debug: bool = False
    path: Path | None = field(default=None, repr=False, compare=False)


def resolve_paths(env: Mapping[str, str] | None = None) -> Paths:
    env = os.environ if env is None else env
    if env.get("CRADLE_HOME"):
        home = Path(env["CRADLE_HOME"]).expanduser()
    elif sys.platform == "win32" and env.get("LOCALAPPDATA"):
        home = Path(env["LOCALAPPDATA"]) / "Cradle"
    elif sys.platform == "darwin" and env.get("HOME"):
        home = Path(env["HOME"]) / "Library" / "Application Support" / "Cradle"
    elif sys.platform not in {"win32", "darwin"} and env.get("XDG_DATA_HOME"):
        home = Path(env["XDG_DATA_HOME"]) / "cradle"
    elif sys.platform not in {"win32", "darwin"} and env.get("HOME"):
        home = Path(env["HOME"]) / ".local" / "share" / "cradle"
    else:
        home = Path.cwd() / "userdata"
    return Paths(home.resolve(), Path(__file__).resolve().parents[1] / "content")


def load_config(path: Path, env: Mapping[str, str] | None = None) -> Config:
    """Missing/corrupt settings default; invalid individual fields default independently."""
    env = os.environ if env is None else env
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    values = {}
    for key, default in (
        ("window_scale", 1),
        ("time_lag", 4),
        ("sound", True),
        ("debug", False),
    ):
        value = raw.get(key, default)
        valid = type(value) is type(default)
        if valid and key == "window_scale":
            valid = 1 <= value <= 3
        if valid and key == "time_lag":
            valid = 0 <= value <= 9
        values[key] = value if valid else default
    if env.get("CRADLE_DEBUG") == "1":
        values["debug"] = True
    return Config(**values, path=path)


def save_config(cfg: Config) -> None:
    if cfg.path is None:
        raise ValueError("Config must be bound to a path by load_config")
    values = asdict(cfg)
    values.pop("path")
    # Re-use the read validator without file access to keep writes in the contract.
    if (
        type(cfg.window_scale) is not int
        or not 1 <= cfg.window_scale <= 3
        or type(cfg.time_lag) is not int
        or not 0 <= cfg.time_lag <= 9
        or type(cfg.sound) is not bool
        or type(cfg.debug) is not bool
    ):
        raise ValueError("Invalid configuration")
    cfg.path.parent.mkdir(parents=True, exist_ok=True)
    temp = cfg.path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(values, indent=2) + "\n", encoding="utf-8", newline="\n")
    temp.replace(cfg.path)
