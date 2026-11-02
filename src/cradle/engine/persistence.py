# Version: 0.2.0 | 2026-11-02
"""Lossless JSON DTOs; validation completes before any live state is replaced."""

from copy import deepcopy
from typing import get_args, get_type_hints
from .errors import SaveError, InvariantBreach
from .rng import SeededRng
from .state import check_invariants
from .types import Profession, Strain, Skill, BodyArea, Severity, MemberDTO


def snapshot(s, rng):
    payload = deepcopy(s)
    payload["expedition"]["ranks"] = {
        str(k): v for k, v in payload["expedition"]["ranks"].items()
    }
    return dict(
        schema_version=1,
        rng_state=rng.state(),
        tick=s["tick"],
        clock_days=s["clock_days"],
        roster=deepcopy(s["roster"]),
        expedition=deepcopy(payload["expedition"]),
        world=dict(
            site_states=deepcopy(s["world"]["sites"]),
            one_time_flags=deepcopy(s["flags"]),
            infamy=s["expedition"]["infamy"],
            milestone=s["milestone"],
            quest_score=s["quest_score"],
        ),
        treasury=s["expedition"]["treasury"],
        config_echo=deepcopy(s["config_echo"]),
        engine=payload,
    )


def validate_member(m):
    if not isinstance(m, dict) or not MemberDTO.__required_keys__ <= m.keys():
        raise SaveError("Missing member fields")
    for key, hint in get_type_hints(MemberDTO).items():
        if key not in m:
            continue
        if hint in (int, bool, str) and type(m[key]) is not hint:
            raise SaveError("Invalid member field " + key)
    if (
        not 1 <= m["id"] <= 27
        or not 1 <= m["level"] <= 20
        or not 0 <= m["credit"] <= 65000
        or len(m["items"]) > 9
    ):
        raise SaveError("Member range violation")
    if m["profession"] not in get_args(Profession) or m["strain"] not in get_args(
        Strain
    ):
        raise SaveError("Unknown member identity")
    if set(m["attrs"]) != {"str", "int", "dex", "con", "cha"} or any(
        type(v) != int or not 1 <= v <= 22 for v in m["attrs"].values()
    ):
        raise SaveError("Invalid attributes")
    if set(m["skills"]) != set(get_args(Skill)) or any(
        type(v) != int or not 0 <= v <= 250 for v in m["skills"].values()
    ):
        raise SaveError("Invalid skills")
    if set(m["body"]) != set(get_args(BodyArea)):
        raise SaveError("Invalid body")
    for a in m["body"].values():
        if (
            a["sev"] not in get_args(Severity)
            or type(a["dmg_taken"]) != int
            or a["dmg_taken"] < 0
        ):
            raise SaveError("Invalid body severity")
    if (
        m["hp_max"] < 1
        or not 0 <= m["hp_cur"] <= m["hp_max"]
        or not 0 <= m["mp_cur"] <= m["mp_max"]
    ):
        raise SaveError("Invalid HP/MP")
    if m["xp"] < 0 or m["age_days"] < 0:
        raise SaveError("Invalid member counters")
    for item in m["items"]:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("item_id"), (int, str))
            or type(item.get("bound")) != bool
            or item.get("skin") not in [None, "bow", "rifle"]
        ):
            raise SaveError("Invalid item")


def validate(doc, regs=None):
    # Structural-only old envelopes are supported by saveio tests; engine restores
    # require the complete lossless snapshot rather than inventing omitted state.
    try:
        s = doc["engine"]
        exp = s["expedition"]
        if (
            type(doc["tick"]) != int
            or doc["tick"] < 0
            or doc["tick"] != s["tick"]
            or doc["clock_days"] != s["clock_days"]
            or doc["config_echo"] != s["config_echo"]
        ):
            raise SaveError("Contradictory save counters/configuration")
        if (
            doc["world"]["one_time_flags"] != s["flags"]
            or doc["world"]["site_states"] != s["world"]["sites"]
            or doc["world"]["infamy"] != exp["infamy"]
            or doc["world"]["quest_score"] != s["quest_score"]
            or doc["world"]["milestone"] != s["milestone"]
        ):
            raise SaveError("Contradictory saved world")
        if s["schema_version"] != 1 or s["phase"] != "post":
            raise SaveError("Continue requires a post snapshot")
        check_invariants(s)
        if (
            s["roster"] != doc["roster"]
            or exp != doc["expedition"]
            or exp["treasury"] != doc["treasury"]
        ):
            raise SaveError("Contradictory save envelope")
        for m in s["roster"]:
            validate_member(m)
        ids = [m["id"] for m in s["roster"]]
        if len(ids) != len(set(ids)) or not set(exp["members"]) <= set(ids):
            raise SaveError("Invalid roster references")
        world = s["world"]
        map_id = world["map_id"]
        pos = world["pos"]
        from .types import MapId

        if (
            map_id not in get_args(MapId)
            or not isinstance(pos, list)
            or len(pos) != 2
            or any(type(v) != int or v < 0 for v in pos)
        ):
            raise SaveError("Invalid map position")
        if regs is not None:
            path = (
                f"world/sites/{map_id}.json"
                if map_id.startswith("site")
                else f"world/{map_id}.json"
            )
            map_doc = regs[path]["rows"][0]
            if pos[0] >= map_doc["width"] or pos[1] >= map_doc["height"]:
                raise SaveError("Map position out of bounds")
            item_ids = {
                r["id"]
                for name in ["items", "tonics", "folio_items", "valuables"]
                for r in regs[f"registries/{name}.json"]["rows"]
            }
            for m in s["roster"]:
                if any(i["item_id"] not in item_ids for i in m["items"]):
                    raise SaveError("Unknown carried item")
                if not set(m["in_use"].values()) <= {i["item_id"] for i in m["items"]}:
                    raise SaveError("Equipped item is not carried")
            if any(i["item_id"] not in item_ids for i in exp["found_items"]):
                raise SaveError("Unknown found item")
        if len(s["automata"]) != 3:
            raise SaveError("Missing automata")
        if s["clock_days"] < 0 or s["tick"] < 0 or exp["infamy"] < 0:
            raise SaveError("Invalid counters")
        # Verify RNG state using an isolated validation instance, not live PRNG.
        SeededRng.validate_snapshot(doc["rng_state"])
    except SaveError:
        raise
    except (KeyError, TypeError, ValueError, AssertionError, InvariantBreach) as exc:
        raise SaveError("Invalid save snapshot") from exc


def restore(doc):
    validate(doc)
    s = deepcopy(doc["engine"])
    s["expedition"]["ranks"] = {int(k): v for k, v in s["expedition"]["ranks"].items()}
    return s, deepcopy(doc["rng_state"])


def site_snapshot(s, site):
    s["world"]["sites"][site]["saved"] = deepcopy(
        {k: v for k, v in s["world"]["sites"][site].items() if k != "saved"}
    )


def site_restore(s, site, mode):
    current = s["world"]["sites"][site]
    if mode == "saved" and current.get("saved"):
        s["world"]["sites"][site] = deepcopy(current["saved"])
    elif mode == "original":
        current.update(explored=[], flags={}, dead_sets=[], open_doors=[], disarmed=[])
    # s.flags deliberately remains separate and monotonic (BR-36).
