# Version: 0.2.0 | 2026-11-02
"""Six-area damage, death, and vital-first cures (BR-30/31)."""

from .support import require


def fresh(e):
    return {area: dict(sev="ok", dmg_taken=0) for area in e.rules["body_areas"]}


def apply_damage(e, m, amount, area=None):
    amount = max(0, int(amount))
    m["hp_cur"] = max(0, m["hp_cur"] - amount)
    if area:
        a = m["body"][area]
        a["dmg_taken"] += amount
        broken, gone = e.rules["body_thresholds"]
        fraction = a["dmg_taken"] / m["hp_max"]
        a["sev"] = (
            "gone"
            if fraction >= gone
            else "broken"
            if fraction >= broken
            else "injured"
            if amount
            else a["sev"]
        )
    if m["hp_cur"] == 0 or any(
        m["body"][k]["sev"] == "gone" for k in ["head", "torso"]
    ):
        m["vital"] = "dead"
        m["hp_cur"] = 0
    elif (
        m.get("ref") == "foe"
        and m["hp_cur"] <= m["hp_max"] * e.rules["unconscious_threshold"]
    ):
        m["vital"] = "unconscious"
    elif m["hp_cur"] <= m["hp_max"] * e.rules["down_threshold"]:
        m["vital"] = "down"
    elif m["vital"] != "hollowed":
        m["vital"] = "okay"
    if "status" in m:
        m["status"] = m["vital"]


def heal(e, m, amount, tier=0):
    if m["vital"] == "dead":
        return
    m["hp_cur"] = min(m["hp_max"], m["hp_cur"] + amount)
    budget = [0, 1, 2, 3, 6][tier]
    for area in e.rules["cure_order"]:
        a = m["body"][area]
        severity = a["sev"]
        cost = {"ok": 0, "injured": 1, "broken": 2, "gone": 3}[severity]
        if cost and budget:
            spent = min(cost, budget)
            remaining = cost - spent
            budget -= spent
            a.update(
                sev=["ok", "injured", "broken", "gone"][remaining],
                dmg_taken=0
                if remaining == 0
                else 1
                if remaining == 1
                else max(1, int(m["hp_max"] * e.rules["body_thresholds"][0])),
            )
    if m["hp_cur"] > m["hp_max"] * e.rules["down_threshold"] and not m.get("frozen"):
        m["vital"] = "okay"


def can_act(e, m, tactic):
    require(m["vital"] not in ["dead", "unconscious"], e.text("dead"))
    if m["body"]["arm_r"]["sev"] in ["broken", "gone"]:
        require(tactic == "parry", e.text("parry_only"))
    if tactic == "fire":
        require(
            not any(
                m["body"][a]["sev"] in ["broken", "gone"]
                for a in ["arm_l", "arm_r", "leg_l", "leg_r"]
            ),
            e.text("cannot_fire"),
        )


def roll_area(e, kind):
    weights = e.rules["ballistics"][kind]
    roll = e.rng.d100()
    total = 0
    for area, w in zip(e.rules["body_areas"], weights):
        total += w
        if roll <= total:
            return area
    return e.rules["body_areas"][-1]
