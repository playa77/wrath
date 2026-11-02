# Version: 0.2.0 | 2026-11-02
import ast
from pathlib import Path
from typing import get_args

import pytest

from cradle.engine import events
from cradle.engine.commands import VERBS, validate
from cradle.engine.errors import DomainError
from cradle.engine.types import MemberDTO, Phase, Strain
from cradle.ui.frame import blank_frame


# Spec §6.1: independent closed vocabulary; D-1 forbids legacy additions.
EXPECTED = {
    "session": "new continue demo save quit_to_menu",
    "util": "backup restore new_game_erase",
    "chr": "begin_recruit pick_strain pick_profession accept reject list purge add drop rename designate_auto",
    "adv": "train train_skill learn_feat",
    "credit": "withdraw deposit",
    "shop": "list buy sell",
    "post": "debrief infirmary use_feat use_item distribute trade inspect leave",
    "trail": "move perform use_tonic inspect camp_rest",
    "site": "move look listen_continue pick_lock spot_trap disarm leave_trap choose exit",
    "enc": "fight accept_surrender parley beg_mercy flee",
    "cmb": "thrust attack slash lunge aim feat parry fire rank redo config",
    "menu": "choose return",
}


def test_closed_command_vocabulary():
    assert set(VERBS) == {
        f"{prefix}.{verb}"
        for prefix, verbs in EXPECTED.items()
        for verb in verbs.split()
    }


@pytest.mark.parametrize("verb", sorted(VERBS))
@pytest.mark.parametrize("phase", get_args(Phase))
def test_command_phase_matrix(verb, phase):
    # WP-1.4 / C-10: phase validation must not mutate the supplied command.
    cmd = {"verb": verb, "actor": None, "args": {}}
    if phase in VERBS[verb][0]:
        assert validate(cmd, phase) is None
    else:
        with pytest.raises(DomainError):
            validate(cmd, phase)
    assert cmd == {"verb": verb, "actor": None, "args": {}}


@pytest.mark.parametrize(
    "cmd",
    [
        None,
        {},
        {"verb": "transfer"},
        {"verb": "post.inspect", "actor": True, "args": {}},
        {"verb": "post.inspect", "actor": 0, "args": {}},
        {"verb": "post.inspect", "actor": 7, "args": {}},
        {"verb": "post.inspect", "args": []},
    ],
)
def test_bad_command_envelope(cmd):
    # Spec §11: malformed inputs are domain rejections.
    with pytest.raises(DomainError):
        validate(cmd, "post")


def test_types_are_field_complete():
    # Spec §8.1 / P-R1.
    assert len(get_args(Strain)) == 15
    assert {
        "body",
        "vital",
        "frozen",
        "spent_mp",
        "trainings_taken",
        "resident_post",
    } <= MemberDTO.__required_keys__


def test_event_kinds_ticks_and_purity():
    # Spec §6.2 / D-2: SFX_FLAG is data only; ticks belong to dispatch.
    batch = [
        events.msg("SYS-1"),
        events.menu("post", {}, []),
        events.state({}),
        events.map_update([]),
        events.combat({}),
        events.sfx_flag("sound"),
        events.save_written("slot1.json"),
        events.ending("good"),
        events.error(DomainError("session.save", "post only")),
    ]
    assert {e["kind"] for e in batch} == {
        "MSG",
        "MENU",
        "STATE",
        "MAP",
        "COMBAT",
        "SFX_FLAG",
        "SAVE_WRITTEN",
        "ENDING",
        "ERROR",
    }
    stamped = events.stamp(batch, 12) + events.stamp(batch, 13)
    assert [e["tick"] for e in stamped] == sorted(e["tick"] for e in stamped)
    assert all(e["tick"] == 0 for e in batch)
    assert batch[-1]["data"] == {"verb": "session.save", "reason": "post only"}


def test_frame_cells_are_independent():
    # C-1 / C-6 / spec §6.3: 120×40, independently allocated stacks.
    a, b = blank_frame(tick=3), blank_frame()
    assert (a["w"], a["h"], a["tick"]) == (120, 40, 3)
    assert len(a["cells"]) == 40 and all(len(row) == 120 for row in a["cells"])
    a["cells"][0][0]["layers"].append(
        {"symbol_id": 300, "fg": "trail", "bg": "ink", "flags": set()}
    )
    assert not a["cells"][0][1]["layers"]
    assert not a["cells"][1][0]["layers"]
    assert not b["cells"][0][0]["layers"]


def test_engine_import_direction():
    # ADR-1 / C-3 / C-6: no presentation, I/O, clock, or secondary RNG in engine.
    root = Path(__file__).resolve().parents[1] / "src" / "cradle" / "engine"
    forbidden = {
        "tcod",
        "ui",
        "render",
        "platform",
        "time",
        "datetime",
        "asyncio",
        "threading",
        "secrets",
    }
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                assert not (set(module.split(".")) & forbidden), (path, module)
                assert module != "random" or path.name == "rng.py"
