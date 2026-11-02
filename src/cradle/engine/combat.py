# Version: 0.2.0 | 2026-11-02
"""Tactics, ranks, ballistics and round resolution (FR-CMB; §8.6)."""

import re
from .support import party, member as get_member, require, emit, credit_money
from . import events, body, feats, encounters, tribunal, outfitter


def start(e, **a):
    c = e.s["combat"]
    e.s["phase"] = "combat"
    if c["sleep_start"]:
        for m in party(e, living=True):
            m["vital"] = "sleeping"
            m["sleep_rounds"] = e.rng.dice(1, 4)
        c["sleep_start"] = False
    return [events.menu("tactic", {"member": party(e, living=True)[0]["id"]}, [])]


def assign(e, member=None, **a):
    # Engine passes the concrete command name, never reads UI input.
    tactic = e.current_verb.split(".")[-1]
    m = get_member(e, member, living=True)
    require(m["id"] in e.s["expedition"]["members"], "runtime_not_in_expedition")
    body.can_act(e, m, tactic)
    c = e.s["combat"]
    require(not c["redo_open"], "runtime_use_return_to_execute_or_redo")
    if tactic == "rank":
        rank = a.get("rank")
        require(rank in e.rules["ranks"], "runtime_invalid_rank")
        e.s["expedition"]["ranks"][m["id"]] = rank
        tactic = "parry"
    if tactic == "feat" and a.get("feat_id") is None:
        return feats.options(e, m, "cmb.feat")
    if tactic == "feat":
        require(not c["wrestle"], "runtime_no_feats_in_the_wrestling_pit")
        feats.can_perform(e, m, a.get("feat_id"))
        a["feat"] = a["feat_id"]
    elif tactic == "fire":
        require(not c["wrestle"], "runtime_bare_hands_only")
        require(
            "fire" in m["in_use"] and outfitter.usable(e, m, m["in_use"]["fire"]),
            "runtime_no_usable_fire_piece",
        )
    elif tactic == "lunge" and m["profession"] != "white_hunter":
        tactic = "thrust"
        a["target_rank"] = 1
    if tactic in e.rules["tactics"]:
        while m["skills"]["attack"] < e.rules["tactics"][tactic].get("min_skill", 0):
            tactic = {"slash": "attack", "attack": "thrust", "aim": "thrust"}[tactic]
    rank = a.get("target_rank", 1)
    require(type(rank) == int and rank >= 1, "runtime_invalid_target_rank")
    if tactic == "lunge":
        require(rank <= 2, "runtime_lunge_reaches_only_rank_two")
    if tactic in ["thrust", "attack", "slash"] and m["profession"] != "cat_burglar":
        require(rank == 1, "runtime_melee_cannot_reach_that_rank")
    c["assign"][m["id"]] = dict(tactic=tactic, **a)
    active = party(e, living=True)
    c["redo_open"] = all(m["id"] in c["assign"] for m in active)
    return [
        events.state({"assigned": m["id"], "tactic": tactic}),
        events.menu(
            "round_ready" if c["redo_open"] else "tactic",
            {
                "member": next(
                    (m["id"] for m in active if m["id"] not in c["assign"]), m["id"]
                )
            },
            [
                dict(key="D", label=e.text("runtime_redo"), verb="cmb.redo", args={}),
                dict(
                    key="ENTER",
                    label=e.text("runtime_execute_round"),
                    verb="menu.return",
                    args={},
                ),
            ]
            if c["redo_open"]
            else [],
        ),
    ]


def redo(e, **a):
    require(e.s["combat"]["redo_open"], "runtime_assign_the_whole_column_first")
    e.s["combat"]["assign"] = {}
    e.s["combat"]["redo_open"] = False
    return [events.menu("tactic", {"member": party(e, living=True)[0]["id"]}, [])]


def field(e, family, side="allies", mid=None):
    return max(
        (
            f["value"]
            for f in e.s["combat"]["fields"]
            if f["family"] == family
            and f["side"] == side
            and f.get("member") in [None, mid]
        ),
        default=0,
    )


def pos_mod(e, m):
    ranks = e.s["expedition"]["ranks"]
    others = [
        e.rules["ranks"].index(ranks.get(t["id"], "middle"))
        for t in party(e, living=True)
        if t["id"] != m["id"]
    ]
    if not others:
        return 0
    own = e.rules["ranks"].index(ranks.get(m["id"], "middle"))
    cap = e.rules["rank_mod"]
    return max(-cap, min(cap, round((sum(others) / len(others) - own) * cap)))


def dice_string(e, value):
    match = re.match(r"(\d+)d(\d+)", value)
    return e.rng.dice(int(match[1]), int(match[2])) if match else 1


def asleep(e, m):
    if m["vital"] != "sleeping":
        return False
    m["sleep_rounds"] = m.get("sleep_rounds", 1) - 1
    if m["sleep_rounds"] <= 0:
        m["vital"] = "okay"
    return True


def player_attack(e, m, assignment):
    c = e.s["combat"]
    tactic = assignment["tactic"]
    if asleep(e, m) or m["vital"] in ["dead", "unconscious"]:
        return []
    if m["body"]["arm_r"]["sev"] in ["broken", "gone"]:
        tactic = "parry"
    if tactic == "feat":
        return feats.perform_combat(
            e, member=m["id"], **{k: v for k, v in assignment.items() if k != "tactic"}
        )
    if tactic == "parry":
        return []
    spec = e.rules["tactics"][tactic]
    swings = spec["swings"] + (int(e.rng.chance(50)) if tactic == "slash" else 0)
    records = []
    for _ in range(swings):
        foes = [f for f in c["foes"] if f["vital"] != "dead"]
        if not foes:
            break
        requested = assignment.get("target_rank", 1)
        target = next((f for f in foes if f["rank"] == requested), foes[0])
        row = e.lookup("menaces", target["menace_id"])
        skill = m["skills"]["marksman" if tactic == "fire" else "attack"]
        bonus = field(e, "pugilist_acc", mid=m["id"])
        if tactic == "fire":
            skill = max(skill, field(e, "marksman", mid=m["id"]))
            bonus += field(e, "loads_acc", mid=m["id"])
        else:
            bonus += pos_mod(e, m)
        bonus += field(e, "paralysis", "foes")
        chance = max(1, min(e.rules["skill_cap"], skill + bonus + spec["acc"]))
        if target["vital"] == "down":
            chance += 25
        hit = target["vital"] == "sleeping" or e.rng.d100() <= chance
        if hit:
            weapon = "fire" if tactic == "fire" else "weapon"
            value = (
                e.items[m["in_use"][weapon]]["value"]
                if weapon in m["in_use"] and not c["wrestle"]
                else 0
            )
            damage = (
                value
                + m["attrs"]["str"] // 4
                + spec["damage"]
                + field(e, "pugilist_damage", mid=m["id"])
            )
            if tactic in ["thrust", "slash"]:
                damage += (1 if e.rng.chance(50) else 0) * (
                    1 if tactic == "thrust" else -1
                )
            if tactic == "fire":
                damage += field(e, "loads_value", mid=m["id"])
            armor = e.rules["armor"].get(str(target["menace_id"]), 0)
            area = body.roll_area(
                e,
                "fire"
                if tactic == "fire"
                else "aim"
                if tactic == "aim"
                else "tall"
                if "tall" in row["flags"]
                else "hand",
            )
            sleeping = target["vital"] == "sleeping"
            body.apply_damage(e, target, max(1, damage - armor), area)
            if sleeping and target["vital"] != "dead" and not e.rng.chance(50):
                target["vital"] = "sleeping"
            records.append(
                dict(
                    member=m["id"],
                    foe=target["id"],
                    damage=max(1, damage - armor),
                    area=area,
                )
            )
    return [events.combat({"hits": records})]


def foe_attack(e, foe):
    living = party(e, living=True) + [
        a for a in e.s["combat"]["allies"] if a["vital"] != "dead"
    ]
    if not living or foe["vital"] in ["dead", "unconscious"] or asleep(e, foe):
        return []
    row = e.lookup("menaces", foe["menace_id"])
    target = e.rng.pick(living)
    if foe["casts_left"] and e.rng.chance(50):
        foe["casts_left"] -= 1
        if e.rng.chance(min(100, field(e, "confusion", "foes"))):
            return []
        ident = e.rng.pick(row["feats"])
        feats.counter_passive(e)
        if ident in [27]:
            target["vital"] = "sleeping"
            target["sleep_rounds"] = e.rng.dice(1, 4)
        elif ident in [28, 29, 30, 41, 42, 46]:
            feats.put_field(e, ident, "slow", 15, side="allies", member=target["id"])
        else:
            maxima = (
                e.rules["feat_fx"]["assault"]
                if 33 <= ident <= 36
                else e.rules["feat_fx"]["sweep"]
            )
            index = ident - 33 if 33 <= ident <= 36 else max(0, min(3, ident - 9))
            body.apply_damage(e, target, e.rng.dice(1, maxima[index]))
        return [
            events.combat({"cast": ident, "foe": foe["id"], "target": target["id"]})
        ]
    assignment = e.s["combat"]["assign"].get(target["id"], {})
    parry = assignment.get("tactic") == "parry"
    chance = (
        50
        + (0 if target.get("ref") == "automaton" else pos_mod(e, target))
        - target.get("evasion", 0)
        - field(e, "surge", mid=target["id"])
        - field(e, "pugilist_defense", mid=target["id"])
        - field(e, "paralysis", "foes")
        - field(e, "dread", "foes") * 5
        + (e.rules["parry_mod"] if parry else 0)
    )
    if target["vital"] == "down":
        chance += 25
    if target["vital"] == "sleeping" or e.rng.d100() <= max(1, chance):
        damage = dice_string(e, row["dmg"]) - field(e, "enervation", "foes")
        armor = (
            target.get("armor", 0)
            + sum(
                e.items[target.get("in_use", {})[k]]["value"]
                for k in ["armor", "shield"]
                if k in target.get("in_use", {}) and (k != "shield" or parry)
            )
            + field(e, "hardening", mid=target["id"])
        )
        body.apply_damage(
            e,
            target,
            max(1, damage - armor),
            body.roll_area(e, "tall" if "tall" in row["flags"] else "hand"),
        )
        return [
            events.combat(
                {
                    "foe": foe["id"],
                    "target": target["id"],
                    "damage": max(1, damage - armor),
                }
            )
        ]
    return []


def run_round(e):
    c = e.s["combat"]
    require(c["redo_open"], "runtime_assign_all_living_members")
    result = []
    for auto in c["allies"]:
        if auto.get("acts_first") and auto["vital"] != "dead":
            foes = [f for f in c["foes"] if f["vital"] != "dead"]
            if foes:
                body.apply_damage(e, foes[0], e.rng.dice(*auto["dmg"]))
    for m in sorted(
        party(e, living=True),
        key=lambda m: e.rules["ranks"].index(
            e.s["expedition"]["ranks"].get(m["id"], "middle")
        ),
    ):
        if e.s["combat"] is None:
            return result
        result += player_attack(e, m, c["assign"][m["id"]])
    if e.s["combat"] is None:
        return result
    for auto in c["allies"]:
        if auto.get("acts_first") or auto["vital"] == "dead":
            continue
        foes = [f for f in c["foes"] if f["vital"] != "dead"]
        if foes:
            body.apply_damage(e, foes[0], e.rng.dice(*auto["dmg"]))
    for foe in c["foes"]:
        result += foe_attack(e, foe)
    if not party(e, living=True):
        return result + aftermath(e, "defeat")
    if all(f["vital"] == "dead" for f in c["foes"]):
        return result + aftermath(e, "victory")
    morale = encounters.morale_check(e)
    if e.s["combat"] is None:
        return result + morale
    c["round"] += 1
    c["assign"] = {}
    c["redo_open"] = False
    # Reorganize surviving foes by rank after every round.
    for rank, foe in enumerate([f for f in c["foes"] if f["vital"] != "dead"], 1):
        foe["rank"] = rank
    e.s["phase"] = "encounter"
    return result + emit("menace") + [events.menu("encounter", {}, [])]


def foes_free_attacks(e):
    result = []
    for foe in e.s["combat"]["foes"]:
        result += foe_attack(e, foe)
    if not party(e, living=True):
        return result + aftermath(e, "defeat")
    return result + start(e)


def treasure(e, tier):
    table = next(
        r for r in e.regs["world/encounters_tables.json"]["treasure"] if r["id"] == tier
    )
    lo, hi = table["dollars"]
    dollars = lo - 1 + e.rng.dice(1, hi - lo + 1)
    result = credit_money(e, dollars)
    e.s["expedition"]["leg_dollars"] += dollars
    if e.rng.chance(table["chance"]):
        choices = [
            r["id"]
            for r in e.items.values()
            if r["family"] in ["weapon", "shield", "armor", "fire"]
            and table["value"][0] <= r["value"] <= table["value"][1]
        ]
        if choices and len(e.s["expedition"]["found_items"]) < e.rules["found_cap"]:
            result += outfitter.give(e, e.rng.pick(choices))
    return result


def aftermath(e, outcome):
    c = e.s["combat"]
    result = []
    if outcome == "defeat":
        return tribunal.judge(e)
    e.s["phase"] = "site" if c["origin_map"].startswith("site") else "trail"
    if outcome == "victory":
        exp = e.s["expedition"]
        exp["leg_xp"] += sum(
            e.lookup("menaces", f["menace_id"])["xp"] for f in c["foes"]
        )
        for tier in sorted(
            set(e.lookup("menaces", f["menace_id"])["treasure"] for f in c["foes"])
        ):
            if e.s["phase"] != "site" or any(
                e.rng.d100() <= m["skills"]["find_item"] for m in party(e, living=True)
            ):
                result += treasure(e, tier)
        if c.get("set_id"):
            site = e.s["world"]["sites"][c["origin_map"]]
            site["dead_sets"].append(c["set_id"])
        e.s["combat"] = None
        from .scripts import execute

        result += execute(e, c["on_win"])
    else:
        e.s["combat"] = None
    return result + [
        events.combat({"outcome": outcome}),
        events.menu(e.s["phase"], {}, []),
    ]
