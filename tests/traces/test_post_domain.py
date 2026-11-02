# Version: 0.2.0 | 2026-11-02
"""Post-domain traces through production commands only (§12a)."""

from copy import deepcopy
import pytest
from tests.harness import Journey
from cradle.engine import persistence
from cradle.engine.errors import SaveError


def test_trace01_03_muster_residence_and_recruit(tmp_path):
    # TRACE-01/02/03; FR-CHR-001–008; BR-3/8.
    j = Journey(tmp_path).muster()
    e = j.e
    assert len(e.s["roster"]) == 6 and e.s["expedition"]["members"] == list(range(1, 7))
    before = deepcopy(e.s)
    rng = e.rng.state()
    assert j.do("chr.add", member=1, allow_error=True)[0]["kind"] == "ERROR"
    assert e.s == before and e.rng.state() == rng
    j.do("chr.rename", member=1, name="Test Hunter")
    j.do("chr.drop", member=6)
    j.do("chr.begin_recruit")
    j.do("chr.pick_strain", strain="STRANGE")
    j.do("chr.pick_profession", prof="white_hunter")
    j.do("chr.accept", name="New Explorer")
    recruit = e.s["roster"][-1]
    assert recruit["strain"] not in [
        "club_stock",
        "crag_folk",
        "lake_folk",
        "mesa_folk",
        "scrub_folk",
    ]
    assert all(
        v <= e.lookup("strains", recruit["strain"])["caps"][k]
        for k, v in recruit["attrs"].items()
    )
    j.do("chr.designate_auto", automaton="air")
    assert e.s["expedition"]["automaton"] == 30
    j.do("chr.purge", member=recruit["id"], confirm=True)
    assert len(e.s["roster"]) == 6
    j.do("chr.list")
    j.do("post.inspect", member=1)


def test_trace04_05_shop_credit_and_kit(tmp_path):
    # TRACE-04/05; FR-TWN-001/002/006; BR-7/8/9/10/35.
    j = Journey(tmp_path).muster()
    e = j.e
    for m in e.s["roster"]:
        j.do("credit.withdraw", member=m["id"], amount=m["credit"])
    total = e.s["expedition"]["treasury"]
    j.do("credit.deposit", amount=6000)
    assert e.s["expedition"]["treasury"] == total - 6000
    j.do("shop.list", member=1, page=0)
    j.do("shop.buy", member=1, item_id="folio_IV")
    j.do("post.use_item", member=1, item="folio_IV")
    j.do("post.trade", src_member=1, dst_member=2, item="folio_IV")
    j.do("shop.sell", member=2, item="folio_IV")
    j.do("shop.buy", member=1, item_id="nerve_tonic_1")
    j.do("post.use_item", member=1, item="nerve_tonic_1")
    j.do("shop.buy", member=1, item_id="armor_1")
    assert e.s["roster"][0]["in_use"]["armor"] == "armor_1"
    before = deepcopy(e.s)
    assert (
        j.do("credit.withdraw", member=1, amount=65001, allow_error=True)[0]["kind"]
        == "ERROR"
    )
    assert e.s == before


def test_trace09_rest_and_rejected_advancement(tmp_path):
    # TRACE-09; FR-ADV-001/003/004; OQ-4 spot values.
    j = Journey(tmp_path).muster()
    e = j.e
    j.do("post.infirmary")
    assert e.s["clock_days"] == 7
    for verb, args in [
        ("adv.train", {"member": 1}),
        ("adv.learn_feat", {"member": 1, "feat_id": 53}),
        ("adv.train_skill", {"member": 1, "skill": "attack"}),
    ]:
        before = deepcopy(e.s)
        assert j.do(verb, allow_error=True, **args)[0]["kind"] == "ERROR"
        assert e.s == before
    from cradle.engine.training import cost

    # OQ-4 formula is tested on the actual dispatch-produced member.
    m = e.s["roster"][0]
    expected = int(
        200 * 2 * ((21 - m["attrs"]["cha"]) / 10) * (1 + 0.05 * m["trainings_taken"])
    )
    assert cost(e, m, 2) == expected


def test_trace12_save_continue_backup_and_corruption(tmp_path):
    # TRACE-12; FR-SAV-001–004; C-10: quit in field resumes at recorded post.
    j = Journey(tmp_path).muster()
    e = j.e
    j.do("session.save", slot=1)
    j.do("post.leave")
    j.do("trail.move", dir="S")
    j.do("session.quit_to_menu")
    j.do("session.continue", slot=1)
    assert e.s["phase"] == "post" and e.s["world"]["pos"] == [37, 24]
    j.do("session.quit_to_menu")
    j.do("util.backup", member=1, slot=1)
    j.do("util.restore", filename="member1.json")
    assert len(e.s["roster"]) == 7
    j.do("util.new_game_erase", confirm=False)
    before = deepcopy(e.s)
    (tmp_path / "saves/slot1.json").write_text("{", encoding="utf-8", newline="\n")
    assert j.do("session.continue", slot=1, allow_error=True)[0]["kind"] == "ERROR"
    assert e.s == before
    j.do("util.new_game_erase", confirm=True)
    assert e.s["phase"] == "post"


@pytest.mark.parametrize(
    "field,value",
    [("treasury", 65001), ("tick", -1), ("roster", []), ("rng_state", {})],
)
def test_semantic_save_rejections(tmp_path, field, value):
    # C-4 / §11: malformed full snapshots never become live game state.
    j = Journey(tmp_path).muster()
    doc = persistence.snapshot(j.e.s, j.e.rng)
    doc[field] = value
    with pytest.raises(SaveError):
        persistence.validate(doc)


def test_projection_is_detached(tmp_path):
    # ADR-1: presentation cannot mutate engine state.
    from cradle.engine.state import project

    j = Journey(tmp_path).muster()
    p = project(j.e.s)
    p["roster"][0]["name"] = "Changed"
    assert j.e.s["roster"][0]["name"] != "Changed"
