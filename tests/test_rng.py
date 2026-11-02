# Version: 0.1.0 | 2026-11-02
import hashlib
import json
from copy import deepcopy

import pytest
from cradle.engine.rng import SeededRng


def draw(rng):
    return [(rng.d100(), rng.dice(2, 6), rng.chance(25), rng.pick(['a', 'b', 'c']))
            for _ in range(100)]


def test_same_seed_and_log(seed):
    # C-3 / ADR-2 / WP-1.3.
    a, b = SeededRng(seed), SeededRng(seed)
    a.tick = b.tick = 23
    a.caller = b.caller = 'combat'
    assert draw(a) == draw(b)
    assert a.log == b.log
    assert len(a.log) == 400
    assert all(row['tick'] == 23 and row['caller'] == 'combat' for row in a.log)
    assert a.replay_hash() == hashlib.sha256(''.join(str(r['result']) for r in a.log).encode()).hexdigest()


def test_restart_equivalence(seed):
    # C-3 / AC-Determinism: snapshot crosses a real JSON serialization boundary.
    original = SeededRng(seed)
    draw(original)
    snapshot = json.loads(json.dumps(original.state()))
    resumed = SeededRng(999)
    resumed.restore(snapshot)
    assert draw(original) == draw(resumed)
    assert original.state() == resumed.state()
    assert original.replay_hash() == resumed.replay_hash()
    snapshot['log'].clear()
    assert len(resumed.log) == 800


def test_boundary_draws_are_logged(seed):
    # WP-1.3: every public draw logs, including certain/impossible chances.
    rng = SeededRng(seed)
    assert not rng.chance(0)
    assert rng.chance(100)
    assert rng.dice(1, 1) == 1
    assert rng.pick([object()]) is not None
    assert len(rng.log) == 4


@pytest.mark.parametrize('call', [lambda r: r.dice(0, 6), lambda r: r.dice(1, 0),
    lambda r: r.dice(True, 6), lambda r: r.chance(-1), lambda r: r.chance(101),
    lambda r: r.chance(True), lambda r: r.pick([])])
def test_bad_draw_does_not_advance(call, seed):
    # Spec §11: validate before mutation.
    rng = SeededRng(seed)
    before = rng.state()
    with pytest.raises(ValueError):
        call(rng)
    assert rng.state() == before


@pytest.mark.parametrize('bad', [None, {}, {'version': 1}, {'internal': []}])
def test_corrupt_snapshot_is_atomic(bad, seed):
    # C-3 / WP-1.3 restart failure preserves live generator.
    rng = SeededRng(seed)
    before = rng.state()
    with pytest.raises(ValueError):
        rng.restore(bad)
    assert rng.state() == before


def test_corrupt_draw_record_is_atomic(seed):
    # WP-1.3: log belongs to the same snapshot transaction as PRNG state.
    rng = SeededRng(seed)
    draw(rng)
    before = rng.state()
    bad = deepcopy(before)
    bad['log'][0]['result'] = 'not an integer'
    with pytest.raises(ValueError):
        rng.restore(bad)
    assert rng.state() == before
