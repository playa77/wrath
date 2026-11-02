# Version: 0.2.0 | 2026-11-02
"""Every feat family is exercised by legitimately advanced members (§12a)."""

from pathlib import Path
from tools.build_campaigns import Campaign
from cradle.simcli import parse_script
from cradle.engine.support import party


def execute_round(j, verb="cmb.parry", caster=None, **args):
    e = j.e
    if e.s["phase"] == "encounter":
        j.do("enc.fight")
    for actor, mid in enumerate(e.s["expedition"]["members"], 1):
        m = next(m for m in e.s["roster"] if m["id"] == mid)
        if m["vital"] == "dead":
            continue
        j.do(
            verb if mid == caster else "cmb.parry",
            actor=actor,
            **(args if mid == caster else {}),
        )
    return j.do("menu.return")


def test_every_normal_feat_routes_through_paid_learning_and_combat(tmp_path):
    # TRACE-09/11; FR-ADV-001–005, FR-MAG-001–005, BR-37, OQ-1/5/17.
    # The fixture is an entire fresh-seed command journey, not a saved state or
    # a fixture granting levels/skills/feats. All learning costs were debited.
    j = Campaign(tmp_path)
    e = j.e
    for _, cmd in parse_script(
        Path(__file__).parents[1] / "golden/advanced_training.txt"
    ):
        j.do(cmd["verb"], actor=cmd["actor"], **cmd["args"])
    expected = set(range(1, 53)) | {54, 55, 56}
    assert expected <= {f for m in party(e) for f in m["feats"]}
    assert all(not m["frozen"] for m in party(e) if m["id"] in [6, 7, 8, 9, 10])
    for feat in sorted(expected - {44}):
        caster = next(m for m in party(e) if feat in m["feats"])
        if caster["vital"] == "dead":
            while caster["vital"] == "dead":
                j.do("post.use_feat", member=8, feat=44, target=caster["id"])
                j.do("post.infirmary")
        j.do("post.infirmary")
        for attempt in range(30):
            j.do("post.leave")
            j.do("trail.move", dir="E")
            for _ in range(150):
                if e.s["phase"] == "encounter":
                    break
                j.do("trail.move", dir="E" if e.s["world"]["pos"][0] == 5 else "W")
            assert e.s["phase"] == "encounter"
            j.do("enc.fight")
            for _ in range(6):
                if caster["vital"] != "sleeping" or e.s["phase"] not in [
                    "combat",
                    "encounter",
                ]:
                    break
                execute_round(j)
            if (
                e.s["phase"] in ["combat", "encounter"]
                and caster["vital"] not in ["dead", "sleeping"]
                and caster["body"]["arm_r"]["sev"] not in ["broken", "gone"]
            ):
                break
            if e.s["phase"] in ["combat", "encounter"]:
                j.settle()
            j.walk((4, 7))
            j.do("post.infirmary")
        assert e.s["phase"] in ["combat", "encounter"], feat
        before = caster["mp_cur"]
        cost = e.lookup("feats", feat)["mp"]
        params = {"feat_id": feat, "target_rank": 1}
        if feat in [1, 2, 3, 4]:
            params["target_member"] = caster["id"]
        if feat == 54:
            params["post"] = 17
        result = execute_round(j, "cmb.feat", caster=caster["id"], **params)
        assert caster["mp_cur"] == before - cost, (feat, result)
        if feat == 48 and e.s["combat"] is not None:
            assert any(a["id"] == 30 for a in e.s["combat"]["allies"])
            execute_round(j)
        if e.s["phase"] in ["combat", "encounter"]:
            j.settle()
        if e.s["phase"] == "trail":
            j.walk((4, 7))
        assert e.s["phase"] == "post", feat
    # Elder Site-domain Boon follows the same dispatcher, with its actual grant.
    j.do("post.infirmary")
    j.do("post.use_feat", member=8, feat=54, post=1)
    j.goto("site01")
    j.do("trail.perform", member=1, feat=58)
    assert e.s["roster"][0]["spent_mp"]
    # Talk tiers, Wood's withdrawal and feat refusals use the same live journey.
    j.do("trail.perform", member=8, feat=54, post=17)
    j.do("post.infirmary")
    j.goto("site09")
    j.point(27, 12)
    j.choose(2)
    assert e.s["phase"] == "encounter"  # pure talk threatens and starts mortal fight
    j.settle()
    j.do("trail.perform", member=8, feat=54, post=1)
    j.do("post.infirmary")
    j.goto("site01")
    j.point(15, 15)
    j.choose(2)
    assert e.s["expedition"]["infamy"] == 2
    j.do("trail.perform", member=8, feat=54, post=4)
    j.do("post.infirmary")
    j.goto("site08")
    j.point(15, 3)
    assert any(
        ev["kind"] == "MSG" and ev["data"]["txt_id"] == "absent"
        for ev in e.event_log[-8:]
    )
    j.do("trail.perform", member=8, feat=54, post=17)
    j.do("post.infirmary")
    for mid in [1, 6]:
        j.do("chr.drop", member=mid)
    j.goto("site09")
    j.point(27, 12)
    j.choose(2)
    assert any(
        ev["kind"] == "MSG" and ev["data"]["txt_id"] == "DLG-081"
        for ev in e.event_log[-5:]
    )
    j.point(27, 11)
    j.point(27, 12)
    j.choose(3)
    j.choose(5)
    assert any(
        ev["kind"] == "MSG" and ev["data"]["txt_id"] == "DLG-083"
        for ev in e.event_log[-5:]
    )
    j.point(27, 11)
    j.point(27, 12)
    j.choose(3)
    j.choose(1)
    assert any(
        ev["kind"] == "MSG" and ev["data"]["txt_id"] == "DLG-084"
        for ev in e.event_log[-5:]
    )
    j.do("trail.perform", member=8, feat=54, post=15)
    j.do("post.infirmary")
    j.goto("site06")
    j.point(8, 12)
    j.choose(2)
    assert e.s["expedition"]["infamy"] == 3
    j.do("trail.perform", member=8, feat=54, post=17)
    j.do("post.infirmary")
    j.goto("site09")
    j.point(27, 12)
    j.choose(2)
    assert any(
        ev["kind"] == "MSG" and ev["data"]["txt_id"] == "DLG-082"
        for ev in e.event_log[-5:]
    )
