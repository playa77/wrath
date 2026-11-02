# Version: 0.2.0 | 2026-11-02
"""Quest progression, infamy and ongoing-play endings (FR-QST; BR-34–36)."""

from .support import party, require, emit, credit_money
from . import events


def infamy_tier(e):
    return (
        0
        if e.s["expedition"]["infamy"] == 0
        else 1
        if e.s["expedition"]["infamy"] < 3
        else 3
    )


def add_infamy(e, n):
    e.s["expedition"]["infamy"] += n


def update_score(e):
    flags = e.s["flags"]
    weights = e.rules["score_weights"]
    raw = sum(
        w
        for k, w in weights.items()
        if flags.get(k)
        or (k == "ending" and (flags.get("ending_good") or flags.get("ending_evil")))
    )
    e.s["quest_score"] = min(100, raw * 100 // sum(weights.values()))


def filmon_consult(e):
    keys = [
        "kilmor_found",
        "funeral_done",
        "met_priestess",
        "drowned_gate_entered",
        "wood_met",
    ]
    stage = 0
    while stage < len(keys) and e.s["flags"].get(keys[stage]):
        stage += 1
    e.s["milestone"] = max(e.s["milestone"], stage + 1)
    return emit("DLG-001") + emit("DLG-002") + emit(f"DLG-{10 + stage:03}")


def debrief(e, **a):
    update_score(e)
    rating = next(
        text for upper, text in e.rules["ratings"] if e.s["quest_score"] <= upper
    )
    return emit(rating, score=e.s["quest_score"])


def end_game(e, kind):
    require(kind in ["good", "evil"], "runtime_unknown_ending")
    if e.s["flags"].get("ending_good") or e.s["flags"].get("ending_evil"):
        return []
    e.s["flags"]["ending_" + kind] = True
    messages = credit_money(e, e.rules["ending_dollars"])
    from .outfitter import give

    for m in party(e, living=True):
        m["xp"] += e.rules["ending_xp"]
        choices = (
            [
                r["id"]
                for r in e.items.values()
                if r["family"] == "weapon" and 20 <= r["value"] <= 25
            ]
            if kind == "good"
            else [e.rules["evil_armor"]]
        )
        messages += give(e, e.rng.pick(choices))
        if kind == "good" and e.s["expedition"]["found_items"]:
            inst = e.s["expedition"]["found_items"][-1]
            inst["elder"] = True
            inst["label"] = "Elder-work " + e.items[inst["item_id"]]["name"]
        if kind == "evil" and e.s["expedition"]["found_items"]:
            e.s["expedition"]["found_items"][-1]["label"] = "Obsidian Regalia"
    if kind == "evil":
        for pool in [m["items"] for m in party(e)] + [e.s["expedition"]["found_items"]]:
            for inst in pool:
                if inst["item_id"] == "obsidian_urn":
                    inst["label"] = "Obsidian Urn shards"
                    inst["curio"] = True
    update_score(e)
    return (
        messages
        + emit("DLG-086" if kind == "good" else "DLG-087")
        + [events.ending(kind)]
    )
