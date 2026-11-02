# Version: 0.2.0 | 2026-11-02
"""Spec §8.1 field-complete domain DTOs; no infrastructure or presentation."""

from typing import Literal, TypedDict, NotRequired

Id = int
Strain = Literal[
    "club_stock",
    "crag_folk",
    "lake_folk",
    "mesa_folk",
    "scrub_folk",
    "hyena_man",
    "albino_tunnel_folk",
    "ratling",
    "sauroid",
    "ape_man",
    "basalt_brute",
    "fen_man",
    "glider_folk",
    "wing_folk",
    "long_man",
]
Profession = Literal[
    "white_hunter",
    "pugilist",
    "expedition_doctor",
    "scout",
    "cat_burglar",
    "antiquarian_mesmerist",
]
Standing = Literal["urchin", "stoker", "artisan", "patrician"]
BodyArea = Literal["head", "torso", "arm_l", "arm_r", "leg_l", "leg_r"]
Severity = Literal["ok", "injured", "broken", "gone"]
Vital = Literal["okay", "sleeping", "down", "unconscious", "dead", "hollowed"]
Skill = Literal[
    "attack",
    "parry",
    "swim",
    "listen",
    "spot_trap",
    "disarm_trap",
    "find_item",
    "pick_lock",
    "marksman",
]
Domain = Literal["everywhere", "post", "field", "site", "combat"]
FeatClass = Literal["passive", "active"]
Terrain = Literal[
    "trail",
    "badlands",
    "swamp",
    "escarpment",
    "river",
    "water",
    "floor",
    "lava",
    "solid",
]
MapId = Literal[
    "province",
    "ziggurat_sun",
    "ziggurat_drowned",
    "deeps",
    "site01",
    "site02",
    "site03",
    "site04",
    "site05",
    "site06",
    "site07",
    "site08",
    "site09",
    "site10",
    "site11",
]
Phase = Literal[
    "boot", "post", "trail", "site", "encounter", "combat", "tribunal", "demo"
]
Rank = Literal["front", "middle", "back"]
Dir = Literal["N", "S", "E", "W"]


class ItemInst(TypedDict):
    item_id: str | int
    skin: Literal["bow", "rifle"] | None
    bound: bool
    elder: NotRequired[bool]
    label: NotRequired[str]
    curio: NotRequired[bool]


class AreaState(TypedDict):
    sev: Severity
    dmg_taken: int


BodyState = dict[BodyArea, AreaState]


class MemberDTO(TypedDict):
    id: Id
    name: str
    strain: Strain
    profession: Profession
    standing: Standing
    attrs: dict[str, int]
    luck: int
    age_days: int
    level: int
    xp: int
    hp_cur: int
    hp_max: int
    mp_cur: int
    mp_max: int
    spent_mp: bool
    skills: dict[Skill, int]
    feats: list[Id]
    slots_left: int
    items: list[ItemInst]
    in_use: dict
    credit: int
    trainings_taken: int
    resident_post: Id
    body: BodyState
    vital: Vital
    frozen: bool
    rites: list[int]
    creation_attr_sum: int
    decline_applied: int
    sleep_rounds: NotRequired[int]


class ExpeditionDTO(TypedDict):
    members: list[Id]
    treasury: int
    found_items: list[ItemInst]
    infamy: int
    leg_xp: int
    leg_dollars: int
    leg_items: int
    time_out_days: int
    automaton: Id | None
    sentry: Id
    ranks: dict[Id, Rank]


class SiteState(TypedDict):
    visited: bool
    explored: list[list[int]]
    flags: dict[str, bool | int]
    dead_sets: list[str]
    original_snapshot: dict | None
    saved: NotRequired[dict]
    open_doors: list[str]
    disarmed: list[str]
    revealed_traps: list[str]
    gate_open: bool
    moves: int


class WorldDTO(TypedDict):
    map_id: MapId
    pos: list[int]
    plane_return: tuple[MapId, int, int] | None
    sites: dict[MapId, SiteState]
    funicular: tuple[str, int, str] | None
    visited_posts: list[Id]


class Combatant(TypedDict):
    ref: Literal["member", "automaton", "foe"]
    id: Id
    rank: Rank | int
    body: BodyState
    status: Vital
    casts_left: int
    hp_cur: int
    hp_max: int


class CombatState(TypedDict):
    round: int
    foes: list[Combatant]
    allies: list[Combatant]
    assign: dict[Id, dict]
    redo_open: bool
    sleep_start: bool
    treasure: dict
    fields: list[dict]


class ActiveFeatFx(TypedDict):
    feat: Id
    family: str
    tier: int
    stacks: int
    side: str


class Automaton(TypedDict):
    id: int
    name: str
    hp: int
    dmg: list[int]
    armor: int
    evasion: int


class GameState(TypedDict):
    schema_version: Literal[1]
    tick: int
    clock_days: int
    phase: Phase
    roster: list[MemberDTO]
    automata: list[Automaton]
    expedition: ExpeditionDTO | None
    world: WorldDTO
    quest_score: int
    milestone: int
    flags: dict[str, bool | int]
    post_context: Id
    combat: CombatState | None
    script_ctx: dict | None
    config_echo: dict
    stock: list[str]
    menu_id: str
    moves: int
    pending_training: dict | None


class SavedWorld(TypedDict):
    site_states: dict[str, dict]
    one_time_flags: dict[str, bool | int]
    infamy: int
    milestone: int
    quest_score: int


class SaveDoc(TypedDict):
    schema_version: Literal[1]
    rng_state: dict
    tick: int
    clock_days: int
    roster: list[MemberDTO]
    expedition: ExpeditionDTO
    world: SavedWorld
    treasury: int
    config_echo: dict
    engine: GameState


class MemberBackup(TypedDict):
    schema_version: Literal[1]
    member: MemberDTO


class SlotInfo(TypedDict):
    slot: int
    exists: bool
    label: str
