# Version: 0.1.0 | 2026-11-02
"""Shared infrastructure; game state must come from Engine.dispatch (§12a)."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def cradle_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate each test from real saves (FR-SAV-001; Doc 2 §12a)."""
    home = tmp_path / "cradle"
    for subdir in ("saves", "backups", "logs"):
        (home / subdir).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CRADLE_HOME", str(home))
    return home


@pytest.fixture
def save_dir(cradle_home: Path) -> Path:
    return cradle_home / "saves"


@pytest.fixture
def seed() -> int:
    """Explicit default seed for deterministic tests (C-3; Doc 2 §12b)."""
    return 7


@pytest.fixture(params=(0, 7, 42))
def seeds(request: pytest.FixtureRequest) -> int:
    """Reusable explicit seed cases; no RNG or game state constructed here."""
    return request.param
