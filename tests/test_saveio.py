# Version: 0.1.0 | 2026-11-02
"""WP-1.6 file-boundary tests; no playable GameState is constructed here."""
import json

import pytest
from cradle.engine.errors import SaveError
from cradle.platform.config import resolve_paths
from cradle.platform import saveio


def envelope():
    # Spec §6.4 structural transport only. Semantic acceptance arrives in WP-3.1.
    return {'schema_version': 1, 'rng_state': {}, 'tick': 0, 'clock_days': 0,
            'roster': [], 'expedition': {}, 'treasury': 0, 'config_echo': {},
            'world': {'site_states': {}, 'one_time_flags': {}, 'infamy': 0,
                      'milestone': 0, 'quest_score': 0}}


def test_slot_json_transport(cradle_home):
    # WP-1.6: JSON serialization, slot naming, read/write ports.
    paths = resolve_paths()
    doc = envelope()
    target = saveio.write_slot(1, doc, paths=paths)
    assert target == paths.saves / 'slot1.json'
    assert saveio.read_slot(1, paths=paths) == doc
    assert '\n  "schema_version"' in target.read_text()
    assert [s['exists'] for s in saveio.list_slots(paths=paths)] == [False, True, False, False, False]


@pytest.mark.parametrize('slot', ['../slot1', '1', True, -1, 5, None])
def test_slot_identifiers_are_not_paths(slot, cradle_home):
    # Doc 1 §7-3: reject path traversal and non-integer slots.
    with pytest.raises(SaveError):
        saveio.write_slot(slot, envelope(), paths=resolve_paths())
    assert not (cradle_home / 'saves').exists()


@pytest.mark.parametrize('contents', ['{', '[]', '{}', '{"schema_version": 999}'])
def test_corrupt_slot_is_save_error(contents, cradle_home):
    # Spec §11: malformed save is a load failure, never partially applied.
    path = cradle_home / 'saves' / 'slot0.json'
    path.parent.mkdir()
    path.write_text(contents)
    with pytest.raises(SaveError):
        saveio.read_slot(0, paths=resolve_paths())
    assert path.read_text() == contents


def test_validator_failure_preserves_old_slot(cradle_home):
    # WP-1.6 / WP-3.1 seam: semantic validation must run before writes.
    paths = resolve_paths()
    target = saveio.write_slot(1, envelope(), paths=paths)
    before = target.read_bytes()

    def reject(doc):
        raise SaveError('semantic rejection')

    with pytest.raises(SaveError, match='semantic rejection'):
        saveio.write_slot(1, envelope(), paths=paths, validator=reject)
    with pytest.raises(SaveError, match='semantic rejection'):
        saveio.read_slot(1, paths=paths, validator=reject)
    assert target.read_bytes() == before


def test_invalid_json_value_preserves_old_slot(cradle_home):
    # C-4: unsupported JSON values cannot truncate a previous save.
    paths = resolve_paths()
    target = saveio.write_slot(1, envelope(), paths=paths)
    before = target.read_bytes()
    bad = envelope()
    bad['config_echo'] = {'bad': float('nan')}
    with pytest.raises(SaveError):
        saveio.write_slot(1, bad, paths=paths)
    assert target.read_bytes() == before


@pytest.mark.parametrize('filename', ['../member1.json', '/tmp/member1.json', 'member0.json',
    'member31.json', 'member01.json', 'member1.json/other', 'member1\\other.json'])
def test_backup_traversal_rejected(filename, cradle_home):
    # FR-SAV-003 / Doc 1 §7-3: exports use a closed filename vocabulary.
    with pytest.raises(SaveError, match='filename'):
        saveio.restore_member(filename, paths=resolve_paths())


def test_corrupt_backup_and_symlink(cradle_home):
    # FR-SAV-003: read validation before handing a member to the engine.
    paths = resolve_paths()
    paths.backups.mkdir()
    backup = paths.backups / 'member1.json'
    backup.write_text(json.dumps({'schema_version': 1, 'member': {}}))
    with pytest.raises(SaveError, match='missing fields'):
        saveio.restore_member(backup.name, paths=paths)
    link = paths.backups / 'member2.json'
    link.symlink_to(backup)
    with pytest.raises(SaveError, match='symlink'):
        saveio.restore_member(link.name, paths=paths)


def test_erase_requires_literal_confirmation_and_preserves_backups(cradle_home):
    # FR-SES-004 / FR-SAV-003: active saves erase only on True; exports survive.
    paths = resolve_paths()
    target = saveio.write_slot(0, envelope(), paths=paths)
    paths.backups.mkdir()
    backup = paths.backups / 'member1.json'
    backup.write_text('separate export')
    for declined in [False, None, 1, 'yes']:
        saveio.erase_all(declined, paths=paths)
        assert target.exists()
    saveio.erase_all(True, paths=paths)
    assert not target.exists()
    assert backup.exists()
