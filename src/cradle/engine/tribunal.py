# Version: 0.2.0 | 2026-11-02
"""Wipe-only judgement and permanent Hollowed status (FR-BOD-005/OQ-11)."""

from .support import party, emit
from . import body


def judge(e):
    results = []
    r = e.rules["defeat_return"]
    e.s["expedition"]["treasury"] = 0
    for m in party(e):
        p = max(
            r["min"],
            min(
                r["max"],
                r["base"]
                + (m["luck"] - r["luck_center"]) * r["luck_factor"]
                + e.s["quest_score"] * r["score_factor"],
            ),
        )
        m["body"] = body.fresh(e)
        if not m["frozen"] and e.rng.d100() <= p * 100:
            m["vital"] = "okay"
            m["hp_cur"] = max(1, int(m["hp_max"] * r["hp_fraction"]))
            m["attrs"]["con"] = max(1, m["attrs"]["con"] - 1)
            results += emit("returned", member=m["id"])
        else:
            m["hp_max"] = max(
                1,
                int(
                    e.lookup("professions", m["profession"])["hp_table"][-1]
                    * (1 + 0.05 * (m["attrs"]["con"] - 10))
                ),
            )
            m.update(
                vital="hollowed",
                level=e.rules["level_cap"],
                frozen=True,
                hp_cur=m["hp_max"],
            )
            results += emit("hollowed", member=m["id"])
    post = e.lookup("posts", e.s["post_context"])
    e.s["world"].update(map_id=post["map_id"], pos=list(post["pos"]))
    e.s.update(phase="post", combat=None, script_ctx=None)
    return results + e.autosave()
