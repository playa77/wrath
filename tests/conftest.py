# Version: 0.1.0 | 2026-11-02
"""WP-0.2: no GameState fixtures; domain setup belongs to dispatch (spec §12a)."""

import pytest


@pytest.fixture
def cradle_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CRADLE_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture
def seed():
    return 7
