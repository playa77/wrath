# Version: 0.2.0 | 2026-11-02
"""AC-CMB: observable fallback/reach/rank behavior through public commands."""

from cradle.engine.combat import pos_mod
from tests.harness import Journey


def test_tactic_fallbacks_reach_and_relative_ranks(tmp_path):
    # FR-CMB-001–004 / BR-13: real starter skills, no manufactured combat state.
    j = Journey(tmp_path).muster()
    e = j.e
    j.do("post.leave")
    for _ in range(100):
        if e.s["phase"] == "post":
            j.do("post.leave")
        j.do("trail.move", dir="N" if e.s["world"]["pos"][1] > 24 else "S")
        if e.s["phase"] == "encounter":
            break
    assert e.s["phase"] == "encounter"
    j.do("enc.fight")
    for m in e.s["roster"][:6]:
        assert pos_mod(e, m) == 0
    j.do("cmb.slash", actor=1)
    assert e.s["combat"]["assign"][1]["tactic"] == "attack"
    j.do("cmb.attack", actor=2)
    assert e.s["combat"]["assign"][2]["tactic"] == "thrust"
    j.do("cmb.aim", actor=3)
    assert e.s["combat"]["assign"][3]["tactic"] == "thrust"
    j.do("cmb.lunge", actor=4, target_rank=2)
    assert e.s["combat"]["assign"][4]["tactic"] == "thrust"
    assert e.s["combat"]["assign"][4]["target_rank"] == 1
    j.do("cmb.thrust", actor=5, target_rank=3)
    j.do("cmb.parry", actor=6)
    assert e.s["combat"]["redo_open"]
    j.do("cmb.redo")
    j.do("cmb.lunge", actor=1, target_rank=2)
    result = j.do("cmb.thrust", actor=2, target_rank=2, allow_error=True)
    assert result[0]["kind"] == "ERROR"
    j.do("cmb.rank", actor=1, rank="front")
    assert pos_mod(e, e.s["roster"][0]) > 0
    for actor in range(2, 7):
        j.do("cmb.rank", actor=actor, rank="front")
    assert all(pos_mod(e, m) == 0 for m in e.s["roster"][:6])
    j.do("cmb.redo")
    assert not e.s["combat"]["assign"]
