# Version: 0.2.0 | 2026-11-02
"""Advancement, three skill lessons and MP growth (OQ-2–5/20)."""

import math
from .support import member as get_member, party, require, credit_money
from . import events


def xp_needed(e, m):
    r = e.data["xp_tables"][0]
    f = r["attribute_factor"]
    attr = max(
        f["min"],
        min(
            f["max"], f["base"] - (m["creation_attr_sum"] - f["offset"]) / f["divisor"]
        ),
    )
    return math.floor(
        r["base"]
        * m["level"]
        * r["strain_factor"][m["strain"]]
        * r["profession_factor"][m["profession"]]
        * attr
    )


def cost_curve(level, cha, trainings, rules, multiplier=1):
    return math.floor(
        rules["training_base"]
        * level
        * ((rules["training_cha_base"] - cha) / rules["training_cha_divisor"])
        * (1 + rules["training_repeat"] * trainings)
        * multiplier
    )


def cost(e, m, level):
    return cost_curve(
        level,
        m["attrs"]["cha"],
        m["trainings_taken"],
        e.rules,
        e.lookup("strains", m["strain"])["fee_multiplier"],
    )


def train(e, member, **a):
    m = get_member(e, member, living=True)
    require(not m["frozen"], e.text("cannot_learn"))
    require(m["level"] < e.rules["level_cap"], "runtime_level_cap")
    require(e.s["pending_training"] is None, "runtime_finish_current_skill_training")
    needed = xp_needed(e, m)
    require(m["xp"] >= needed, f"{e.text('xp_needed')}: {max(0, needed - m['xp'])}")
    payment = cost(e, m, m["level"] + 1)
    require(e.s["expedition"]["treasury"] >= payment, e.text("afford"))
    e.s["expedition"]["treasury"] -= payment
    m["xp"] -= needed
    m["level"] += 1
    p = e.lookup("professions", m["profession"])
    m["hp_max"] = max(
        1,
        math.floor(
            p["hp_table"][m["level"] - 1] * (1 + 0.05 * (m["attrs"]["con"] - 10))
        ),
    )
    m["hp_cur"] = min(m["hp_cur"], m["hp_max"])
    m["slots_left"] = max(
        0,
        p["feat_rate"] * m["level"] + max(0, m["attrs"]["int"] - 10) - len(m["feats"]),
    )
    shares = e.data["starting_tables"][0]["share_by_standing"]
    credit_money(e, e.rules["training_award"] * m["level"] * shares[m["standing"]])
    e.s["pending_training"] = dict(
        member=member, left=e.rules["training_skills"], repeats={}
    )
    return [events.state({"trained": member, "level": m["level"]})]


def train_skill(e, member, skill, **a):
    ctx = e.s["pending_training"]
    require(ctx is not None and ctx["member"] == member, "runtime_no_training_session")
    m = get_member(e, member)
    require(skill in m["skills"], "runtime_unknown_skill")
    rep = ctx["repeats"].get(skill, 0)
    increments = e.rules["skill_increments"]
    m["skills"][skill] = min(
        e.rules["skill_cap"],
        m["skills"][skill] + increments[min(rep, len(increments) - 1)],
    )
    ctx["repeats"][skill] = rep + 1
    ctx["left"] -= 1
    if not ctx["left"]:
        m["trainings_taken"] += e.rules["training_skills"]
        e.s["pending_training"] = None
    return [events.state({"skill": skill, "value": m["skills"][skill]})]


def learn_feat(e, member, feat_id=None, **a):
    m = get_member(e, member, living=True)
    require(not m["frozen"], e.text("cannot_learn"))
    matrix = e.lookup("feat_matrix", m["profession"])
    offered = [i for row in matrix["levels"][: m["level"]] for i in row]
    if feat_id is None:
        choices = [
            e.lookup("feats", n)
            for n in offered
            if n not in m["feats"] and not e.lookup("feats", n)["vacant"]
        ]
        require(choices and m["slots_left"] > 0, e.text("no_feats"))
        return [
            events.menu(
                "learn_feats",
                {"member": member},
                [
                    dict(
                        key=str(i + 1),
                        label=f"{f['name']} ({f['mp']} MP)",
                        verb="adv.learn_feat",
                        args={"member": member, "feat_id": f["id"]},
                    )
                    for i, f in enumerate(choices)
                ],
            )
        ]
    f = e.lookup("feats", feat_id)
    require(
        not f["vacant"]
        and feat_id in offered
        and feat_id not in m["feats"]
        and m["slots_left"] > 0,
        e.text("no_feats"),
    )
    payment = math.floor(
        e.rules["feat_cost"]
        * f["mp"]
        * (
            (e.rules["training_cha_base"] - m["attrs"]["cha"])
            / e.rules["training_cha_divisor"]
        )
        * e.lookup("strains", m["strain"])["fee_multiplier"]
    )
    require(e.s["expedition"]["treasury"] >= payment, e.text("afford"))
    e.s["expedition"]["treasury"] -= payment
    m["feats"].append(feat_id)
    m["slots_left"] -= 1
    return [events.state({"learned": feat_id})]


def mp_growth(e, m):
    ceiling = e.lookup("professions", m["profession"])["mp_table"][m["level"] - 1]
    if (
        m["spent_mp"]
        and not m["frozen"]
        and m["mp_max"] < ceiling
        and e.rng.chance(e.rules["mp_growth_pct"])
    ):
        m["mp_max"] += 1
    m["spent_mp"] = False


def divide_xp(e):
    members = party(e, living=True)
    exp = e.s["expedition"]
    share = exp["leg_xp"] // len(members) if members else 0
    for m in members:
        m["xp"] += share
    exp.update(leg_xp=0, leg_dollars=0, leg_items=0, time_out_days=0)
    return [events.state({"xp_share": share})]
