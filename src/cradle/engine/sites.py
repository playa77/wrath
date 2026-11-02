# Version: 0.2.0 | 2026-11-02
"""Progressive maps, doors, hidden panels and traps (FR-DGN; BR-36)."""

from .support import party, require, held, emit
from . import events, scripts, persistence, body, timekeep, encounters
from .trail import DIRECTIONS


def context(e):
    return e.s["world"]["sites"][e.s["world"]["map_id"]]


def definition(e):
    return e.lookup(e.s["world"]["map_id"], e.s["world"]["map_id"])


def key(pos):
    return ",".join(map(str, pos))


def enter(e, site, mode="saved"):
    doc = e.lookup(site, site)
    require(party(e), e.text("no_party"))
    world = e.s["world"]
    if not world["map_id"].startswith("site"):
        world["plane_return"] = [world["map_id"], *world["pos"]]
    if site not in world["sites"]:
        world["sites"][site] = dict(
            visited=True,
            explored=[],
            flags={},
            dead_sets=[],
            original_snapshot=None,
            open_doors=[],
            disarmed=[],
            revealed_traps=[],
            gate_open=False,
            moves=0,
        )
    else:
        persistence.site_restore(e.s, site, mode)
    # Refillable camp pens deliberately reset; once-ever flags live in s.flags.
    for row in doc["sets"]:
        if row.get("refill") and row["id"] in world["sites"][site]["dead_sets"]:
            world["sites"][site]["dead_sets"].remove(row["id"])
    world.update(map_id=site, pos=list(doc["entry"]))
    e.s["phase"] = "site"
    e.s["script_ctx"] = None
    if site == "site09":
        e.s["flags"]["fastness_reached"] = True
    result = look(e) + scripts.run_square(e, site, *world["pos"])
    return result + [events.menu("site", {}, [])] if not e.s["script_ctx"] else result


def move(e, dir, **a):
    require(dir in DIRECTIONS, "runtime_invalid_direction")
    require(
        not (e.s["script_ctx"] and e.s["script_ctx"].get("kind") == "script"),
        "runtime_answer_the_current_prompt_first",
    )
    doc = definition(e)
    st = context(e)
    x, y = e.s["world"]["pos"]
    dx, dy = DIRECTIONS[dir]
    pos = [x + dx, y + dy]
    x, y = pos
    require(0 <= x < doc["width"] and 0 <= y < doc["height"], e.text("blocked"))
    terrain = doc["grid"][y][x]
    require(terrain not in ["wall", "solid"], e.text("blocked"))
    # Gate barriers apply to the whole interior, so authored corridors cannot
    # accidentally bypass a hard key/strain gate.
    site = e.s["world"]["map_id"]
    if site == "site06" and y < 22:
        require(held(e, "sun_key"), e.text("DLG-060"))
    if site == "site07" and y < 22:
        require(st.get("gate_open"), e.text("DLG-062"))
    if site == "site04" and y < 22:
        require(
            any(m["strain"] in ["crag_folk", "mesa_folk"] for m in party(e)),
            e.text("DLG-041"),
        )
    door = next((d for d in doc["doors"] if d["at"] == pos), None)
    if door and key(pos) not in st["open_doors"]:
        st["pending_door"] = pos
        if door["kind"] == "unpickable":
            return emit("unpickable")
        if door["kind"] == "locked":
            return emit("runtime_pick_the_lock_to_proceed")
        if door["kind"] == "enclave":
            require(
                any(m["strain"] in ["crag_folk", "mesa_folk"] for m in party(e)),
                e.text("DLG-041"),
            )
        listener = max(party(e, living=True), key=lambda m: m["skills"]["listen"])
        if e.rng.d100() <= listener["skills"]["listen"]:
            st["door_continue"] = pos
            return [
                events.menu(
                    "listen",
                    {},
                    [
                        dict(
                            key="Y",
                            label=e.text("runtime_proceed"),
                            verb="site.listen_continue",
                            args={"proceed": True},
                        ),
                        dict(
                            key="N",
                            label=e.text("runtime_turn_back"),
                            verb="site.listen_continue",
                            args={"proceed": False},
                        ),
                    ],
                )
            ]
        st["open_doors"].append(key(pos))
    return finish_move(e, pos)


def finish_move(e, pos):
    doc = definition(e)
    st = context(e)
    e.s["world"]["pos"] = list(pos)
    st["moves"] += 1
    if st["moves"] % e.rules["site_day_moves"] == 0:
        timekeep.advance(e, 1)
    result = look(e)
    trap = next(
        (t for t in doc["traps"] if t["at"] == pos and key(pos) not in st["disarmed"]),
        None,
    )
    if trap:
        result += trigger(e, trap)
    if e.s["phase"] != "site":
        return result
    result += scripts.run_square(e, doc["id"], *pos)
    if (
        e.s["phase"] == "site"
        and not e.s["script_ctx"]
        and pos not in doc["safe_route"]
        and doc["pool"]
        and e.rng.pick(list(range(e.rules["site_rate"][1]))) < e.rules["site_rate"][0]
    ):
        rows = [
            e.lookup("menaces", i)
            for i in doc["pool"]
            if "unique" not in e.lookup("menaces", i)["flags"]
        ]
        if rows:
            row = e.rng.pick(rows)
            result += encounters.begin_set(
                e,
                {"foes": [row["id"]] * e.rng.pick(list(range(1, row["pack_max"] + 1)))},
            )
    return result


def look(e, **a):
    doc = definition(e)
    st = context(e)
    px, py = e.s["world"]["pos"]
    radius = e.rules["los_radius"]
    explored = {tuple(p) for p in st["explored"]}
    for y in range(max(0, py - radius), min(doc["height"], py + radius + 1)):
        for x in range(max(0, px - radius), min(doc["width"], px + radius + 1)):
            # Integer interpolation traces a ray; reveal the first blocker only.
            distance = max(abs(x - px), abs(y - py))
            visible = True
            for i in range(1, distance + 1):
                xx = round(px + (x - px) * i / distance)
                yy = round(py + (y - py) * i / distance)
                if (
                    doc["grid"][yy][xx] in ["wall", "door", "panel"]
                    and i < distance
                    and key([xx, yy]) not in st["open_doors"]
                ):
                    visible = False
                    break
            if visible:
                explored.add((x, y))
    st["explored"] = [list(p) for p in sorted(explored)]
    return [events.map_update(st["explored"])]


def listen_continue(e, proceed, **a):
    st = context(e)
    require("door_continue" in st, "runtime_no_listening_prompt")
    pos = st.pop("door_continue")
    if proceed:
        st["open_doors"].append(key(pos))
        return finish_move(e, pos)
    return [events.menu("site", {}, [])]


def pick_lock(e, member=None, **a):
    from .support import member as get_member

    st = context(e)
    require(st.get("pending_door"), "runtime_no_adjacent_lock")
    pos = st["pending_door"]
    door = next(d for d in definition(e)["doors"] if d["at"] == pos)
    require(
        door["kind"] not in ["unpickable", "sun", "drowned", "enclave"],
        e.text("unpickable"),
    )
    m = get_member(e, member, living=True)
    if e.rng.d100() <= m["skills"]["pick_lock"]:
        st["open_doors"].append(key(pos))
        return emit("runtime_the_lock_opens")
    return emit("runtime_the_lock_holds")


def spot_trap(e, **a):
    st = context(e)
    px, py = e.s["world"]["pos"]
    best = max(party(e, living=True), key=lambda m: m["skills"]["spot_trap"])
    found = []
    for trap in definition(e)["traps"]:
        if (
            max(abs(trap["at"][0] - px), abs(trap["at"][1] - py))
            <= e.rules["los_radius"]
            and e.rng.d100() <= best["skills"]["spot_trap"]
        ):
            if key(trap["at"]) not in st["revealed_traps"]:
                st["revealed_traps"].append(key(trap["at"]))
            st["pending_trap"] = trap
            found.append(trap)
    return [events.state({"traps": found})]


def disarm(e, member=None, **a):
    from .support import member as get_member

    st = context(e)
    trap = st.get("pending_trap")
    require(trap is not None, "runtime_no_detected_trap")
    m = get_member(e, member, living=True)
    if e.rng.d100() <= m["skills"]["disarm_trap"]:
        st["disarmed"].append(key(trap["at"]))
        return emit("runtime_trap_disarmed")
    return trigger(e, trap)


def leave_trap(e, **a):
    context(e).pop("pending_trap", None)
    return [events.menu("site", {}, [])]


def trigger(e, trap):
    spec = e.rules["traps"][trap["kind"]]
    members = party(e, living=True)
    selected = (
        members[-spec["targets"] :] if spec.get("rear") else members[: spec["targets"]]
    )
    for m in selected:
        body.apply_damage(e, m, e.rng.dice(*spec["dice"]), spec["area"])
    if not party(e, living=True):
        from .tribunal import judge

        return judge(e)
    return [events.state({"trap_triggered": trap["kind"]})]


def exit(e, save_state=True, **a):
    st = context(e)
    if st["moves"] < e.rules["site_day_moves"]:
        timekeep.advance(e, 1)
    if save_state:
        persistence.site_snapshot(e.s, e.s["world"]["map_id"])
    dest = e.s["world"]["plane_return"]
    require(dest is not None, "runtime_missing_site_return_position")
    e.s["world"].update(map_id=dest[0], pos=dest[1:])
    e.s.update(phase="trail", script_ctx=None)
    return [events.menu("trail", {}, [])]
