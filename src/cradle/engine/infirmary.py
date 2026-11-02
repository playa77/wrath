# Version: 0.2.0 | 2026-11-02
"""Post and rest-house recovery (FR-TWN-004/FR-WLD-004)."""

from .support import party, require
from . import events, body, training, timekeep


def stay(e, resthouse=False, **a):
    if resthouse:
        require(e.s["expedition"]["treasury"] >= e.rules["rest_cost"], e.text("afford"))
        e.s["expedition"]["treasury"] -= e.rules["rest_cost"]
    for m in party(e, living=True):
        training.mp_growth(e, m)
        m["mp_cur"] = m["mp_max"]
        body.heal(e, m, m["hp_max"], 2)
    timekeep.advance(e, e.rules["rest_days"])
    return [events.state({"rested": True})]
