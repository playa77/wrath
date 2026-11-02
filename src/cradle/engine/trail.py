# Version: 0.2.0 | 2026-11-02
"""Terrain traversal, hazards, camps and approach prompts (FR-WLD)."""

from .support import party, require
from . import events, timekeep, body, encounters, outfitter, feats

DIRECTIONS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}


def step(e, dir, **a):
    require(dir in DIRECTIONS, "runtime_invalid_direction")
    require(party(e), e.text("no_party"))
    require(
        not (e.s["script_ctx"] and e.s["script_ctx"].get("kind") == "script"),
        "runtime_answer_the_current_prompt_first",
    )
    world = e.s["world"]
    doc = e.lookup(world["map_id"], world["map_id"])
    dx, dy = DIRECTIONS[dir]
    x, y = world["pos"]
    x += dx
    y += dy
    require(0 <= x < doc["width"] and 0 <= y < doc["height"], e.text("blocked"))
    terrain = doc["grid"][y][x]
    # Escarpment interiors are difficult but passable; only the border cliff is
    # impassable, resolving Doc 2's movement/terrain conflict in favor of FR-WLD.
    require(
        terrain not in ["water", "wall", "solid"]
        and not (
            terrain == "escarpment"
            and (x in [0, doc["width"] - 1] or y in [0, doc["height"] - 1])
        ),
        e.text("blocked"),
    )
    world["pos"] = [x, y]
    e.s["moves"] += 1
    timekeep.advance(e, e.rules["travel_days"].get(terrain, 1))
    result = [events.map_update([[x, y]])]
    if terrain == "river":
        for m in party(e, living=True):
            if e.rng.d100() > m["skills"]["swim"]:
                body.apply_damage(e, m, e.rng.dice(*e.rules["drowning"]))
    if terrain == "lava":
        for m in party(e, living=True):
            body.apply_damage(e, m, e.rng.dice(*e.rules["lava_burn"]))
    if not party(e, living=True):
        from .tribunal import judge

        return result + judge(e)
    feature = next((f for f in doc["features"] if f["pos"] == [x, y]), None)
    if feature:
        if feature["kind"] == "post":
            return result + e.arrive(e.lookup("posts", feature["id"]))
        if feature["kind"] == "resthouse":
            e.s["script_ctx"] = dict(
                kind="script",
                id="resthouse",
                special=None,
                tail=[],
                options=[
                    dict(label=e.text("runtime_stay_275"), then=[]),
                    dict(label=e.text("runtime_leave"), then=[]),
                ],
            )
            return result + [
                events.menu(
                    "resthouse",
                    {},
                    [
                        dict(
                            key="1",
                            label=e.text("runtime_stay_275"),
                            verb="menu.choose",
                            args={"resthouse": True},
                        ),
                        dict(
                            key="2",
                            label=e.text("runtime_leave"),
                            verb="menu.return",
                            args={},
                        ),
                    ],
                )
            ]
        if feature["kind"] == "site":
            e.s["script_ctx"] = dict(kind="site_approach", site=feature["id"])
            return result + [
                events.menu(
                    "enter_site",
                    {},
                    [
                        dict(
                            key="Y",
                            label="Enter " + feature["name"],
                            verb="menu.choose",
                            args={"option_key": "Y"},
                        ),
                        *(
                            [
                                dict(
                                    key="O",
                                    label=e.text("runtime_enter_original_site"),
                                    verb="menu.choose",
                                    args={"option_key": "Y", "mode": "original"},
                                )
                            ]
                            if feature["id"] in world["sites"]
                            else []
                        ),
                        dict(
                            key="N",
                            label=e.text("runtime_leave"),
                            verb="menu.choose",
                            args={"option_key": "N"},
                        ),
                    ],
                )
            ]
        if feature["kind"] == "return":
            world.update(
                map_id="province",
                pos=list(e.lookup("province", "province")["features"][0]["pos"]),
            )
            # Return to the actual Funicular Station, not the nearest post.
            world["pos"] = [58, 22]
            return result
    band = (
        1 + max(abs(x // 15 - 2), abs(y // 10 - 2))
        if world["map_id"] == "province"
        else 4
    )
    table = e.lookup(
        "encounters_tables",
        terrain
        if terrain in ["trail", "badlands", "swamp", "escarpment", "river"]
        else "floor",
    )
    if table["denominator"] and e.rng.pick(list(range(table["denominator"]))) == 0:
        return result + encounters.begin_random(e, table["id"], band)
    if e.s["moves"] % e.rules["camp_interval"] == 0:
        result += camp_rest(e, terrain=table["id"], band=band)
    return result


def camp_rest(e, terrain=None, band=1, **a):
    require(party(e), e.text("no_party"))
    timekeep.advance(e, e.rules["camp_days"])
    if e.rng.pick(list(range(e.rules["camp_ambush"][1]))) < e.rules["camp_ambush"][0]:
        sentry = next(
            (
                m
                for m in party(e, living=True)
                if m["id"] == e.s["expedition"]["sentry"]
            ),
            party(e, living=True)[0],
        )
        asleep = e.rng.d100() > sentry["skills"]["listen"]
        return encounters.begin_ambush(e, terrain or "trail", band, asleep)
    return [events.state({"camped": True})]


def perform(e, **a):
    return feats.perform(e, **a)


def use_tonic(e, tonic=None, item=None, **a):
    return outfitter.use_item(e, item=tonic or item, **a)


def inspect(e, **a):
    return [
        events.state(
            {
                "expedition": e.s["expedition"],
                "members": party(e),
                "clock_days": e.s["clock_days"],
            }
        )
    ]
