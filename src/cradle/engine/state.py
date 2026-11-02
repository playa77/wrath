# Version: 0.2.0 | 2026-11-02
"""Game aggregate and immutable projection (BR-7/8; ADR-1/4)."""

from .support import thaw
import json
from .errors import InvariantBreach


def new_game(seed=0, rules=None):
    return dict(
        schema_version=1,
        tick=0,
        clock_days=0,
        phase="post",
        roster=[],
        automata=thaw(rules["automata"]) if rules else [],
        expedition=dict(
            members=[],
            treasury=0,
            found_items=[],
            infamy=0,
            leg_xp=0,
            leg_dollars=0,
            leg_items=0,
            time_out_days=0,
            automaton=None,
            sentry=1,
            ranks={},
        ),
        world=dict(
            map_id="province",
            pos=[37, 24],
            plane_return=None,
            sites={},
            funicular=None,
            visited_posts=[],
        ),
        quest_score=0,
        milestone=0,
        flags={},
        post_context=1,
        combat=None,
        script_ctx=None,
        config_echo=dict(window_scale=1, time_lag=4, sound=True, debug=False),
        stock=[],
        menu_id="boot",
        moves=0,
        pending_training=None,
    )


def check_invariants(s):
    exp = s["expedition"]
    checks = [
        len(s["roster"]) <= 27,
        len(exp["members"]) <= 6,
        len(set(exp["members"])) == len(exp["members"]),
        len(exp["found_items"]) <= 90,
        0 <= exp["treasury"] <= 65000,
        0 <= s["quest_score"] <= 100,
    ]
    for m in s["roster"]:
        checks.extend(
            [
                len(m["items"]) <= 9,
                0 <= m["credit"] <= 65000,
                1 <= m["level"] <= 20,
                0 <= m["hp_cur"] <= m["hp_max"],
                0 <= m["mp_cur"] <= m["mp_max"],
            ]
        )
    if not all(checks):
        raise InvariantBreach("Game aggregate invariant failed")


def clone(s):
    """Clone the JSON-native aggregate in C; preserve integer runtime map keys."""
    result = json.loads(json.dumps(s, ensure_ascii=False, separators=(",", ":")))
    if result.get("expedition"):
        result["expedition"]["ranks"] = {
            int(k): v for k, v in result["expedition"]["ranks"].items()
        }
    if result.get("combat"):
        result["combat"]["assign"] = {
            int(k): v for k, v in result["combat"]["assign"].items()
        }
    return result


def project(s):
    # Snapshot is detached: presentation cannot mutate engine-owned dictionaries.
    return clone(s)
