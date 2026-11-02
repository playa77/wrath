# Version: 0.2.0 | 2026-11-02
"""Complete feat-family router and passive/active interaction (FR-MAG; BR-37)."""

from .support import member as get_member, party, require, emit, thaw
from . import events, body


def can_perform(e, m, feat, phase=None):
    f = e.lookup("feats", feat)
    phase = phase or e.s["phase"]
    domain = {"trail": "field", "encounter": "combat"}.get(phase, phase)
    require(
        not f["vacant"] and (feat in m["feats"] or feat in m.get("rites", [])),
        "runtime_feat_is_not_known",
    )
    require(f["domain"] in ["everywhere", domain], "runtime_wrong_feat_domain")
    require(m["mp_cur"] >= f["mp"], "runtime_insufficient_mp")
    body.can_act(e, m, "feat")
    return f


def put_field(e, feat, family, value, side="allies", member=None):
    fields = e.s["combat"]["fields"]
    existing = next(
        (
            f
            for f in fields
            if f["family"] == family and f["side"] == side and f.get("member") == member
        ),
        None,
    )
    if family == "dread" and existing:
        existing["value"] += value
    elif existing:
        existing.update(feat=feat, value=max(existing["value"], value))
    else:
        fields.append(
            dict(feat=feat, family=family, value=value, side=side, member=member)
        )
    if family == "surge":
        fields[:] = [
            f for f in fields if not (f["family"] == "slow" and f["side"] == side)
        ]


def counter_passive(e):
    fields = e.s["combat"]["fields"]
    passive = next(
        (
            f
            for f in fields
            if e.lookup("feats", f["feat"])["class"] == "passive"
            and f["side"] == "allies"
        ),
        None,
    )
    if passive:
        fields.remove(passive)


def options(e, m, command):
    domain = {"trail": "field", "encounter": "combat"}.get(e.s["phase"], e.s["phase"])
    offered = [
        e.lookup("feats", n)
        for n in m["feats"] + m.get("rites", [])
        if e.lookup("feats", n)["domain"] in ["everywhere", domain]
    ]
    require(offered, e.text("no_feats"))
    return [
        events.menu(
            "perform_feats",
            {"member": m["id"]},
            [
                dict(
                    key=str(i + 1),
                    label=f"{f['name']} ({f['mp']} MP)",
                    verb=command,
                    args=(
                        {"feat_id": f["id"]}
                        if command == "cmb.feat"
                        else {"member": m["id"], "feat": f["id"]}
                    ),
                )
                for i, f in enumerate(offered)
            ],
        )
    ]


def perform(
    e,
    member=None,
    feat=None,
    feat_id=None,
    target=None,
    target_member=None,
    target_rank=None,
    **a,
):
    m = get_member(e, member, living=True)
    ident = feat if feat is not None else feat_id
    if ident is None:
        return options(
            e,
            m,
            "trail.perform" if e.s["phase"] in ["trail", "site"] else "post.use_feat",
        )
    f = can_perform(e, m, ident)
    fx = e.rules["feat_fx"]
    target_id = target_member or target or m["id"]
    if ident == 54 and not a.get("post"):
        return [
            events.menu(
                "recall",
                {"member": m["id"]},
                [
                    dict(
                        key=str(p["id"]),
                        label=p["name"],
                        verb="trail.perform"
                        if e.s["phase"] in ["site", "trail"]
                        else "post.use_feat",
                        args={"member": m["id"], "feat": 54, "post": p["id"]},
                    )
                    for p in e.data["posts"]
                ],
            )
        ]
    m["mp_cur"] -= f["mp"]
    m["spent_mp"] = True
    if ident in [1, 2, 3, 4]:
        t = get_member(e, target_id, living=True)
        body.heal(e, t, e.rng.dice(1, fx["suture"][ident - 1]), ident)
        return [events.state({"healed": t["id"]})]
    if ident == 44:
        t = get_member(e, target_id)
        require(t["vital"] == "dead", "runtime_target_is_alive")
        if e.rng.chance(fx["revive_pct"]):
            t["attrs"]["con"] = max(1, t["attrs"]["con"] - e.rng.dice(1, 2))
            t["body"] = body.fresh(e)
            t["vital"] = "okay"
            t["hp_cur"] = max(1, t["hp_max"] // 2)
        return [events.state({"revivification": t["vital"] != "dead"})]
    if ident == 58:
        for t in party(e, living=True):
            body.heal(e, t, t["hp_max"], 2)
        return [events.state({"boon": True})]
    if ident == 54:
        p = e.lookup("posts", a["post"])
        return e.arrive(p)
    require(e.s["combat"] is not None, "runtime_no_combat_targets")
    foes = [f for f in e.s["combat"]["foes"] if f["vital"] != "dead"]
    rank = target_rank or 1
    target_foes = [f for f in foes if f["rank"] == rank] or foes[:1]
    if ident in list(range(5, 13)) + list(range(33, 41)):
        family = (
            "lancet"
            if ident <= 8
            else "sweep"
            if ident <= 12
            else "assault"
            if ident <= 36
            else "vitriol"
        )
        start = {"lancet": 5, "sweep": 9, "assault": 33, "vitriol": 37}[family]
        for foe in foes if family == "sweep" else target_foes:
            damage = e.rng.dice(1, fx[family][ident - start])
            armor = (
                e.rules["armor"].get(str(foe["menace_id"]), 0)
                if family == "sweep"
                else 0
            )
            body.apply_damage(
                e,
                foe,
                max(1, damage - armor),
                None
                if family == "assault" or family == "sweep"
                else body.roll_area(e, "feat"),
            )
    elif ident in [13, 14, 15]:
        index = ident - 13
        owner = None if ident == 14 else m["id"]
        put_field(e, ident, "loads_acc", fx["loads_acc"][index], member=owner)
        put_field(e, ident, "loads_value", fx["loads_value"][index], member=owner)
    elif ident in [16, 17]:
        put_field(
            e,
            ident,
            "marksman",
            fx["trance_marksman"],
            member=m["id"] if ident == 16 else None,
        )
    elif 18 <= ident <= 21:
        put_field(e, ident, "surge", fx["surge"][ident - 18])
    elif 22 <= ident <= 25:
        put_field(e, ident, "hardening", fx["hardening"][ident - 22])
    elif ident == 26:
        from .combat import aftermath

        return aftermath(e, "avoided")
    elif ident == 27:
        for foe in target_foes:
            if foe["vital"] != "sleeping" and e.rng.chance(fx["sleep_pct"]):
                foe["vital"] = "sleeping"
                foe["sleep_rounds"] = e.rng.dice(1, 4)
    elif ident == 28:
        put_field(e, ident, "dread", 1, side="foes")
    elif 29 <= ident <= 32:
        put_field(e, ident, "confusion", fx["confusion"][ident - 29], side="foes")
    elif ident in [41, 42, 45]:
        put_field(
            e,
            ident,
            "enervation",
            fx["enervation"][[41, 42, 45].index(ident)],
            side="foes",
        )
    elif ident in [46, 47, 50]:
        put_field(
            e,
            ident,
            "paralysis",
            fx["paralysis"][[46, 47, 50].index(ident)],
            side="foes",
        )
    elif ident == 43:
        from .combat import aftermath

        return aftermath(e, "fled")
    elif ident == 48:
        aid = e.s["expedition"]["automaton"]
        require(aid is not None, "runtime_designate_an_automaton_first")
        auto = thaw(next(x for x in e.s["automata"] if x["id"] == aid))
        auto.update(
            hp_cur=auto["hp"],
            hp_max=auto["hp"],
            vital="okay",
            body=body.fresh(e),
            ref="automaton",
            acts_first=aid == 30,
        )
        if not any(x["id"] == aid for x in e.s["combat"]["allies"]):
            e.s["combat"]["allies"].append(auto)
    elif ident == 49:
        for foe in foes:
            if "M" in e.lookup("menaces", foe["menace_id"])["flags"]:
                foe.update(vital="dead", hp_cur=0)
                foe["banished"] = e.rng.chance(fx["counter_flee"])
    elif ident == 51:
        for t in party(e):
            if t["vital"] == "sleeping":
                t["vital"] = "okay"
    elif ident == 52:
        result = []
        for foe in foes:
            row = e.lookup("menaces", foe["menace_id"])
            tier = e.rules["tier_order"].index(row["tier"])
            if e.rng.chance(fx["assessment_wrong"]):
                tier = max(
                    0, min(len(e.rules["tier_order"]) - 1, tier + e.rng.pick([-1, 1]))
                )
            result.append(
                dict(
                    id=foe["id"],
                    tier=e.rules["tier_order"][tier],
                    hp_band=foe["hp_cur"] // 10 * 10,
                )
            )
        return [events.state({"assessment": result})]
    elif ident in [55, 56]:
        index = ident - 55
        for family, key in [
            ("pugilist_acc", "pugilist_acc"),
            ("pugilist_damage", "pugilist_damage"),
            ("pugilist_defense", "pugilist_defense"),
        ]:
            put_field(e, ident, family, fx[key][index], member=m["id"])
    elif ident == 57:
        from .scripts import climax

        if e.s["world"]["map_id"] == "site09" and any(
            foe["menace_id"] in [75, 76] for foe in e.s["combat"]["foes"]
        ):
            return climax(e)
        return emit("DLG-084")
    return [events.state({"performed": ident})]


def perform_combat(e, **a):
    return perform(e, **a)
