# Version: 0.2.0 | 2026-11-02
"""Calendar aging; thresholds applied once per member (OQ-6)."""

from .support import party


def advance(e, days):
    e.s["clock_days"] += days
    if e.s["phase"] != "post":
        e.s["expedition"]["time_out_days"] += days
    for m in party(e):
        m["age_days"] += days
        st = e.lookup("strains", m["strain"])
        years = m["age_days"] / e.rules["year_days"]
        reached = sum(
            years >= st["lifespan_years"] * mark for mark in st["decline_marks"]
        )
        for stage in range(m["decline_applied"], reached):
            for attr in ["str", "dex", "con"]:
                m["attrs"][attr] = max(
                    1, m["attrs"][attr] - e.rules["decline_physical"][stage]
                )
            if stage == len(st["decline_marks"]) - 1:
                for attr in ["int", "cha"]:
                    m["attrs"][attr] = max(1, m["attrs"][attr] - 1)
        m["decline_applied"] = reached
