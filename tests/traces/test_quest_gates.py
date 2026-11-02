# Version: 0.2.0 | 2026-11-02
"""BR-34 / OQ-7: real key/infamy gate matrix and protected panel traversal."""

from pathlib import Path
from tools.build_campaigns import Campaign
from cradle.simcli import parse_script


def prefix(j, site):
    for _, cmd in parse_script(Path(__file__).parents[1] / "golden/golden_good.txt"):
        j.do(cmd["verb"], actor=cmd["actor"], **cmd["args"])
        if j.e.s["world"]["map_id"] == site:
            return
    raise AssertionError("Site entry was never reached")


def change_city(j, sun):
    if j.e.s["phase"] == "site":
        j.do("site.exit", save_state=True)
    j.walk((9, 8))
    j.goto("site05")
    j.point(4, 13)
    j.choose(39 if sun else 40)
    j.point(26, 13)
    j.choose(1)
    j.goto("site06" if sun else "site07")


def test_drowned_key_and_infamy_matrix(tmp_path):
    # FR-QST-015/016; BR-34; OQ-7: pure/stained barred, blackened welcomed.
    j = Campaign(tmp_path)
    prefix(j, "site06")
    e = j.e
    j.do("site.exit", save_state=True)
    j.walk((9, 6))
    j.do("post.infirmary")
    j.do("session.save", slot=3)
    for count in range(4):
        j.do("session.quit_to_menu")
        j.do("session.continue", slot=3)
        j.goto("site06")
        for x in [8, 15, 22][:count]:
            j.point(x, 12)
            j.choose(2)
        assert e.s["expedition"]["infamy"] == count
        change_city(j, False)
        j.choose(2)
        assert e.s["world"]["sites"]["site07"]["gate_open"] == (count >= 3)
        if count < 3:
            result = j.do("site.move", dir="N", allow_error=True)
            assert result[0]["kind"] == "ERROR"
            j.point(15, 23)
            j.point(15, 22)
            j.choose(3)
            assert not e.s["world"]["sites"]["site07"]["gate_open"]
    # A real Sun-Key-backed visit to D2 supplies the key for the clean bypass.
    j.do("session.quit_to_menu")
    j.do("session.continue", slot=3)
    j.goto("site02")
    j.point(3, 21)
    j.do("site.exit", save_state=True)
    j.goto("site05")
    j.point(4, 13)
    j.choose(40)
    j.point(26, 13)
    j.choose(1)
    j.goto("site07")
    j.choose(3)
    assert (
        e.s["world"]["sites"]["site07"]["gate_open"]
        and e.s["expedition"]["infamy"] == 0
    )


def test_fastness_documented_panel_route_has_no_encounters(tmp_path):
    # TRACE-11 / FR-QST-021: every documented panel, zero random or set combat.
    j = Campaign(tmp_path)
    prefix(j, "site09")
    e = j.e
    draw_count = len(e.rng.log)
    for target in [
        [4, 12],
        [6, 10],
        [8, 12],
        [10, 10],
        [12, 12],
        [14, 10],
        [16, 10],
        [16, 8],
        [27, 8],
        [27, 12],
    ]:
        while e.s["world"]["pos"] != target:
            x, y = e.s["world"]["pos"]
            tx, ty = target
            direction = "E" if x < tx else "W" if x > tx else "S" if y < ty else "N"
            j.do("site.move", dir=direction)
            assert e.s["phase"] == "site" and e.s["combat"] is None
    assert len(e.rng.log) == draw_count
    assert e.s["script_ctx"]["id"] == "voss"
