# Version: 0.1.0 | 2026-11-02
"""Phase 0 installation and test-infrastructure acceptance checks."""

import importlib
from importlib.metadata import distribution
import os
from pathlib import Path

import pytest


@pytest.mark.parametrize('package', [
    'cradle', 'cradle.engine', 'cradle.ui', 'cradle.render', 'cradle.platform',
    'cradle.content.registries', 'cradle.content.world.sites',
    'cradle.content.world.scripts', 'cradle.content.text',
    'cradle.content.presentation',
])
def test_packages_import(package):
    # C-6/ADR-1: package boundaries are present without loading future systems.
    assert importlib.import_module(package).__file__


def test_installed_entry_points():
    # C-1; Doc 2 §13: verify installation metadata, not deferred implementations.
    dist = distribution('cradle')
    entries = {ep.name: ep.value for ep in dist.entry_points
               if ep.group == 'console_scripts'}
    assert entries == {
        'cradle': 'cradle.main:main',
        'cradle-content-check': 'cradle.platform.contentload:check_main',
    }
    assert set(dist.metadata['Requires-Python'].split(',')) == {'>=3.12', '<3.13'}


def test_save_fixture(cradle_home, save_dir):
    # FR-SAV-001: tests cannot write to the player's save location.
    assert Path(os.environ['CRADLE_HOME']) == cradle_home
    assert save_dir == cradle_home / 'saves'
    assert all((cradle_home / name).is_dir()
               for name in ('saves', 'backups', 'logs'))
    assert list(save_dir.iterdir()) == []


def test_explicit_seeds(seed, seeds):
    # C-3; Doc 2 §12b: deterministic test inputs are explicit.
    assert seed == 7
    assert isinstance(seeds, int)


def test_blocklist_loads():
    # C-8: the closed lexeme list from Doc 2 §5.0 must survive verbatim.
    path = Path(__file__).parent / 'fixtures' / 'lint_blocklist.txt'
    terms = [line.strip() for line in path.read_text(encoding='utf-8').splitlines()
             if line.strip() and not line.lstrip().startswith('#')]
    assert terms == ['magic', 'spell', 'god', 'divine', 'undead', 'zombie']


def test_engine_import_direction():
    # C-6/ADR-1: engine must never depend on presentation modules.
    import ast

    engine_dir = Path(importlib.import_module('cradle.engine').__file__).parent
    for source in engine_dir.rglob('*.py'):
        tree = ast.parse(source.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or '']
                names.extend(alias.name for alias in node.names)
            for name in names:
                assert not {'ui', 'render'}.intersection(name.split('.')), (
                    f'{source}:{node.lineno}: engine imports presentation: {name}'
                )
