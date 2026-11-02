# Version: 0.2.0 | 2026-11-02
"""Spec §6.1 closed command vocabulary and phase-only routing contract."""

from typing import TypedDict, get_args
from .errors import DomainError
from .types import Phase


class Command(TypedDict):
    verb: str
    actor: int | None
    args: dict


ALL_PHASES = frozenset(get_args(Phase))
POST = frozenset({"post"})
FIELD = frozenset({"trail"})
SITE = frozenset({"site"})
ENCOUNTER = frozenset({"encounter"})
COMBAT = frozenset({"combat"})
VERBS: dict[str, tuple[frozenset[Phase], str]] = {}


def _register(prefix: str, phases: frozenset[Phase], handlers: dict[str, str]) -> None:
    for verb, path in handlers.items():
        VERBS[f"{prefix}.{verb}"] = (phases, path)


_register(
    "session",
    frozenset({"boot", "demo"}),
    {
        "new": "core.session_new",
        "continue": "core.session_continue",
        "demo": "core.session_demo",
    },
)
VERBS["session.save"] = (POST, "core.session_save")
VERBS["session.quit_to_menu"] = (ALL_PHASES, "core.quit_to_menu")
_register(
    "util",
    frozenset({"boot"}),
    {
        "backup": "core.backup_member",
        "restore": "core.restore_member",
        "new_game_erase": "core.new_game_erase",
    },
)
_register(
    "chr",
    POST,
    {
        "begin_recruit": "creation.begin_recruit",
        "pick_strain": "creation.pick_strain",
        "pick_profession": "creation.pick_profession",
        "accept": "creation.accept",
        "reject": "creation.reject",
        "list": "roster.list_members",
        "purge": "roster.purge",
        "add": "roster.add_to_expedition",
        "drop": "roster.drop",
        "rename": "roster.rename",
        "designate_auto": "roster.designate_automaton",
    },
)
_register(
    "adv",
    POST,
    {
        "train": "training.train",
        "train_skill": "training.train_skill",
        "learn_feat": "training.learn_feat",
    },
)
_register("credit", POST, {"withdraw": "credit.withdraw", "deposit": "credit.deposit"})
_register(
    "shop",
    POST,
    {"list": "outfitter.list_page", "buy": "outfitter.buy", "sell": "outfitter.sell"},
)
_register(
    "post",
    POST,
    {
        "debrief": "quests.debrief",
        "infirmary": "infirmary.stay",
        "use_feat": "feats.perform",
        "use_item": "outfitter.use_item",
        "distribute": "outfitter.distribute",
        "trade": "outfitter.trade",
        "inspect": "roster.inspect",
        "leave": "core.leave_post",
    },
)
_register(
    "trail",
    FIELD,
    {
        "move": "trail.step",
        "perform": "trail.perform",
        "use_tonic": "trail.use_tonic",
        "inspect": "trail.inspect",
        "camp_rest": "trail.camp_rest",
    },
)
_register(
    "site",
    SITE,
    {
        "move": "sites.move",
        "look": "sites.look",
        "listen_continue": "sites.listen_continue",
        "pick_lock": "sites.pick_lock",
        "spot_trap": "sites.spot_trap",
        "disarm": "sites.disarm",
        "leave_trap": "sites.leave_trap",
        "choose": "scripts.choose",
        "exit": "sites.exit",
    },
)
_register(
    "enc",
    ENCOUNTER,
    {
        "fight": "encounters.fight",
        "accept_surrender": "encounters.accept_surrender",
        "parley": "encounters.parley",
        "beg_mercy": "encounters.beg_mercy",
        "flee": "encounters.flee",
    },
)
_register(
    "cmb",
    COMBAT,
    {
        **{
            name: "combat.assign"
            for name in (
                "thrust",
                "attack",
                "slash",
                "lunge",
                "aim",
                "feat",
                "parry",
                "fire",
                "rank",
            )
        },
        "redo": "combat.redo",
        "config": "core.configure",
    },
)
_register(
    "menu", ALL_PHASES, {"choose": "core.menu_choose", "return": "core.menu_return"}
)


def validate(cmd: Command, phase: Phase) -> None:
    """Only validates the envelope; handlers check arguments and rule gates before mutation."""
    if not isinstance(cmd, dict):
        raise DomainError("", "runtime_command_must_be_an_object")
    verb = cmd.get("verb")
    if not isinstance(verb, str) or verb not in VERBS:
        raise DomainError(str(verb), "runtime_unknown_verb")
    if phase not in VERBS[verb][0]:
        raise DomainError(verb, f"not legal during {phase}")
    actor = cmd.get("actor")
    if actor is not None and (type(actor) is not int or not 1 <= actor <= 6):
        raise DomainError(verb, "runtime_actor_must_be_a_column_index_in_1_6")
    if not isinstance(cmd.get("args"), dict):
        raise DomainError(verb, "runtime_args_must_be_an_object")


# FR-MAG-001 Everywhere/Site utilities share the production field entry points.
for _verb in ("trail.perform", "trail.use_tonic"):
    VERBS[_verb] = (FIELD | SITE, VERBS[_verb][1])

# FR-QST-019 quartermaster is a site vendor using the ordinary shop handlers.
for _verb in ("shop.list", "shop.buy", "shop.sell"):
    VERBS[_verb] = (POST | SITE, VERBS[_verb][1])
