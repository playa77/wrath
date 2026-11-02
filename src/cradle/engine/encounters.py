# Version: 0.2.0 | 2026-11-02
"""Approach, diplomatic exits, surrender and random warden (FR-ENC)."""

from .support import require, party, emit
from . import events, body


def begin_set(e, set_def):
    foes = []
    for ident in set_def["foes"]:
        row = e.lookup("menaces", ident)
        foes.append(
            dict(
                id=len(foes) + 1,
                menace_id=ident,
                ref="foe",
                rank=len(foes) + 1,
                name=row["name"],
                body=body.fresh(e),
                vital="okay",
                status="okay",
                hp_cur=row["hp"],
                hp_max=row["hp"],
                casts_left=row["cast_budget"],
                fields=[],
                sleep_rounds=0,
            )
        )
    e.s["combat"] = dict(
        round=1,
        foes=foes,
        allies=[],
        assign={},
        redo_open=False,
        sleep_start=set_def.get("sleep_start", False),
        treasure={},
        fields=[],
        origin_phase=e.s["phase"],
        origin_map=e.s["world"]["map_id"],
        initial_count=len(foes),
        set_id=set_def.get("set_id"),
        on_win=set_def.get("on_win", []),
        wrestle=set_def.get("wrestle", False),
    )
    e.s["phase"] = "encounter"
    return emit("menace") + [
        events.state({"foes": foes}),
        events.menu("encounter", {}, []),
    ]


def begin_random(e, terrain, band):
    table = e.lookup("encounters_tables", terrain)
    ids = [
        i
        for i in table["pool"]
        if e.lookup("menaces", i)["band_min"] <= band
        and "unique" not in e.lookup("menaces", i)["flags"]
    ]
    if not ids:
        return []
    row = e.lookup("menaces", e.rng.pick(ids))
    count = e.rng.pick(list(range(1, row["pack_max"] + 1)))
    return begin_set(e, {"foes": [row["id"]] * count})


def begin_ambush(e, terrain, band, sleep_start):
    result = begin_random(e, terrain, band)
    if result:
        e.s["combat"]["sleep_start"] = sleep_start
    return result


def fight(e, **a):
    from .combat import start

    return start(e)


def accept_surrender(e, **a):
    c = e.s["combat"]
    dead = sum(f["vital"] == "dead" for f in c["foes"])
    require(
        dead / c["initial_count"] >= e.rules["surrender"],
        "runtime_the_menaces_refuse_to_surrender",
    )
    from .combat import aftermath

    return aftermath(e, "victory")


def parley(e, **a):
    disp = e.lookup("menaces", e.s["combat"]["foes"][0]["menace_id"])["disp"]
    from .combat import aftermath

    return (
        aftermath(e, "avoided") if e.rng.chance(e.rules["parley"][disp]) else fight(e)
    )


def beg_mercy(e, **a):
    own = sum(m["hp_cur"] for m in party(e))
    other = sum(m["hp_cur"] for m in e.s["combat"]["foes"])
    chance = e.rules["mercy_weak"] if own <= other else e.rules["mercy_strong"]
    if not e.rng.chance(chance):
        return fight(e)
    exp = e.s["expedition"]
    exp["treasury"] = 0
    del exp["found_items"][: e.rules["mercy_items"]]
    from .combat import aftermath

    return aftermath(e, "mercy")


def flee(e, **a):
    from .combat import aftermath, foes_free_attacks

    return (
        aftermath(e, "fled") if e.rng.chance(e.rules["flee"]) else foes_free_attacks(e)
    )


def morale_check(e):
    c = e.s["combat"]
    dead = sum(f["vital"] == "dead" for f in c["foes"])
    if dead / c["initial_count"] >= e.rules["morale_losses"]:
        disp = e.lookup("menaces", c["foes"][0]["menace_id"])["disp"]
        chance = e.rules["morale_savage"] if disp == "S" else e.rules["morale_chance"]
        if e.rng.chance(chance):
            from .combat import aftermath

            return aftermath(e, "victory")
    return []
