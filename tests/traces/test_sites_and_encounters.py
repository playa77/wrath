# Version: 0.2.0 | 2026-11-02
"""TRACE-06/07/08; FR-DGN/ENC; script and service alternate branches."""

from copy import deepcopy
import pytest
from tools.build_campaigns import Campaign
from tests.harness import Journey


def test_trace08_original_reset_does_not_regrant_and_lock_trap_paths(tmp_path):
    # TRACE-08; FR-DGN-001–006; BR-35/36: dispatch-built site state only.
    j = Campaign(tmp_path)
    j.make_hollowed()
    j.goto("site01")
    e = j.e
    j.point(10, 16)
    assert e.s["milestone"] == 1
    j.point(15, 15)
    j.choose(1)
    j.choose(3)
    j.choose(3)
    j.choose(4)
    assert e.s["flags"]["shrine_boon"]
    assert e.s["expedition"]["treasury"] == 50
    j.point(2, 2)
    j.choose(2)
    assert not e.s["flags"].get("site01.resonator")
    j.point(2, 3)
    j.point(2, 2)
    j.choose(1)
    # Detect and attempt to disarm one nearby trap. Failed disarm is observable
    # damage, not a second member's implicit attempt.
    j.point(12, 17)
    for _ in range(80):
        j.do("site.spot_trap")
        if e.s["world"]["sites"]["site01"].get("pending_trap"):
            break
    assert e.s["world"]["sites"]["site01"].get("pending_trap")
    j.do("site.disarm", member=1)
    j.do("site.leave_trap")
    # A locked door first records an adjacent lock; repeat legitimate attempts.
    j.point(4, 4)
    j.do("site.move", dir="N")
    for _ in range(100):
        j.do("site.pick_lock", member=1)
        if "4,3" in e.s["world"]["sites"]["site01"]["open_doors"]:
            break
    assert "4,3" in e.s["world"]["sites"]["site01"]["open_doors"]
    j.do("site.exit", save_state=True)
    j.goto("site01", mode="original")
    assert e.s["flags"]["shrine_boon"] and e.s["flags"]["site01.resonator"]
    assert e.s["roster"][0]["rites"].count(58) == 1
    j.point(2, 2)
    assert e.s["script_ctx"] is None


def test_enclave_strain_gate_is_atomic(tmp_path):
    # BR-34 / FR-QST-011: charter status alone never substitutes for strain gate.
    j = Campaign(tmp_path)
    j.make_hollowed()
    j.goto("site04")
    e = j.e
    before = deepcopy(e.s)
    result = j.do("site.move", dir="N", allow_error=True)
    assert result[0]["kind"] == "ERROR" and "crag-folk" in result[0]["data"]["reason"]
    assert e.s == before


@pytest.mark.parametrize(
    "verb", ["enc.parley", "enc.beg_mercy", "enc.accept_surrender"]
)
def test_contact_alternative_paths(tmp_path, verb):
    # FR-ENC-003/004/005: refusal preserves rules; diplomacy uses production RNG.
    j = Journey(tmp_path).muster()
    j.do("post.leave")
    for _ in range(100):
        if j.e.s["phase"] == "post":
            j.do("post.leave")
        pos = j.e.s["world"]["pos"]
        j.do("trail.move", dir="N" if pos[1] > 24 else "S")
        if j.e.s["phase"] == "encounter":
            break
    assert j.e.s["phase"] == "encounter"
    result = j.do(verb, allow_error=verb == "enc.accept_surrender")
    if verb == "enc.accept_surrender":
        assert result[0]["kind"] == "ERROR"
    else:
        assert result and j.e.s["phase"] in ["combat", "trail"]


def test_initial_feats_use_combat_and_rest_paths(tmp_path):
    # FR-MAG-001/002/005; BR-37; TRACE-09 MP-spent rest path.
    j = Journey(tmp_path).muster()
    e = j.e
    j.do("post.use_feat", member=2, feat=1, target=1)
    assert e.s["roster"][1]["spent_mp"]
    j.do("post.infirmary")
    assert not e.s["roster"][1]["spent_mp"]
    j.do("post.debrief")
    j.do("post.leave")
    for _ in range(100):
        if e.s["phase"] == "post":
            j.do("post.leave")
        j.do("trail.move", dir="N" if e.s["world"]["pos"][1] > 24 else "S")
        if e.s["phase"] == "encounter":
            break
    j.do("enc.fight")
    # Assign every slot; documented ready/redo stage precedes execution.
    for actor, feat in [(1, 5), (2, None), (3, 5), (4, 52), (5, None), (6, 55)]:
        j.do(
            "cmb.feat" if feat else "cmb.parry",
            actor=actor,
            **({"feat_id": feat} if feat else {}),
        )
    j.do("cmb.redo")
    for actor, feat in [(1, 5), (2, None), (3, 5), (4, 52), (5, None), (6, 55)]:
        j.do(
            "cmb.feat" if feat else "cmb.parry",
            actor=actor,
            **({"feat_id": feat} if feat else {}),
        )
    j.do("menu.return")
    assert e.s["phase"] in ["encounter", "site", "trail", "post"]


@pytest.mark.parametrize("funded", [False, True])
def test_resthouse_stay_and_leave_are_operable(tmp_path, funded):
    # FR-WLD-004 / BR-11: stay charges $275; decline must clear the prompt.
    j = Campaign(tmp_path)
    j.make_hollowed()
    e = j.e
    if funded:
        j.do("credit.withdraw", member=1, amount=275)
    j.do("post.leave")
    j.walk((33, 14))
    assert e.s["script_ctx"]["id"] == "resthouse"
    if funded:
        before = e.s["clock_days"]
        j.do("menu.choose", resthouse=True)
        assert e.s["clock_days"] == before + 7 and e.s["expedition"]["treasury"] == 0
    else:
        assert (
            j.do("menu.choose", resthouse=True, allow_error=True)[0]["kind"] == "ERROR"
        )
        j.do("menu.return")
    assert e.s["script_ctx"] is None
    j.do("trail.move", dir="W")


def test_site_exit_prompt_and_pending_menu_return(tmp_path):
    # FR-DGN-006: saved/original/leave prompts remain operable with keyboard flow.
    j = Campaign(tmp_path)
    j.make_hollowed()
    j.goto("site01")
    result = j.do("menu.choose", site_exit_prompt=True)
    assert result[0]["data"]["menu_id"] == "leave_site"
    assert {o["args"].get("save_state") for o in result[0]["data"]["slots"]} == {
        True,
        False,
        None,
    }
    j.point(15, 15)
    j.do("menu.return")
    assert j.e.s["script_ctx"]["id"] == "shrine"
    result = j.choose(4)
    assert result[-1]["data"]["menu_id"] == "site" and j.e.s["script_ctx"] is None
