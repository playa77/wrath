# Version: 0.2.0 | 2026-11-02
"""Production recruitment and starter roster (FR-CHR-001/002; BR-3)."""

from .support import require, thaw
from . import body, events


def roll_member(e, strain, prof, mid):
    st = e.lookup("strains", strain)
    p = e.lookup("professions", prof)
    start = e.data["starting_tables"][0]
    require(
        st["kind"] == "charter" or prof in st["professions_allowed"],
        "runtime_profession_unavailable_for_this_strain",
    )
    attrs = {
        k: min(st["caps"][k], max(3, e.rng.dice(*start["creation_dice"]) + v))
        for k, v in zip(st["caps"], p["attr_mods"])
    }
    weights = (
        start["strange_weights"] if st["kind"] == "strange" else p["standing_weights"]
    )
    roll = e.rng.d100()
    cumulative = 0
    standing = start["standings"][-1]
    for name, weight in zip(start["standings"], weights):
        cumulative += weight
        if roll <= cumulative:
            standing = name
            break
    attrs["cha"] = max(3, attrs["cha"] + st["impression_cha_delta"])
    skills = thaw(start["starting_skills"][prof])
    for adds in [
        start["strain_skill_adds"].get(strain, {}),
        start["profession_skill_adds"].get(prof, {}),
    ]:
        for k, v in adds.items():
            skills[k] += v
    hp = p["hp_table"][0]
    mp = p["mp_table"][0]
    kit = [
        dict(
            item_id=i,
            skin="bow" if e.items[i]["family"] == "fire" else None,
            bound=False,
        )
        for i in p["start_kit"]
    ]
    matrix = e.lookup("feat_matrix", prof)
    feats = [matrix["levels"][0][0]]
    return dict(
        id=mid,
        name="",
        strain=strain,
        profession=prof,
        standing=standing,
        attrs=attrs,
        luck=7 + e.rng.dice(1, 6),
        age_days=int(
            st["lifespan_years"] * e.rules["year_days"] * start["age_lifespan_fraction"]
        ),
        level=1,
        xp=0,
        hp_cur=hp,
        hp_max=hp,
        mp_cur=mp,
        mp_max=mp,
        spent_mp=False,
        skills=skills,
        feats=feats,
        rites=[],
        slots_left=max(0, p["feat_rate"] + max(0, attrs["int"] - 10) - 1),
        items=kit,
        in_use={e.items[i]["family"]: i for i in p["start_kit"]},
        credit=start["credit_by_standing"][standing],
        trainings_taken=0,
        resident_post=e.s["post_context"],
        body=body.fresh(e),
        vital="okay",
        frozen=False,
        creation_attr_sum=sum(attrs.values()),
        decline_applied=0,
    )


def starter_six(e):
    start = e.data["starting_tables"][0]
    for mid, (strain, prof, name) in enumerate(
        zip(
            start["starter_strains"],
            start["starter_professions"],
            start["starter_names"],
        ),
        1,
    ):
        m = roll_member(e, strain, prof, mid)
        m["name"] = name
        e.s["roster"].append(m)


def begin_recruit(e, **a):
    require(len(e.s["roster"]) < e.rules["roster_cap"], "runtime_roster_full")
    e.s["script_ctx"] = {"recruit": {}}
    return [events.menu("strain", {}, [])]


def pick_strain(e, strain, **a):
    require(
        e.s["script_ctx"] is not None and "recruit" in e.s["script_ctx"],
        "runtime_begin_recruitment_first",
    )
    if strain.upper() == "STRANGE":
        strain = e.rng.pick(
            [s["id"] for s in e.data["strains"] if s["kind"] == "strange"]
        )
    e.lookup("strains", strain)
    e.s["script_ctx"]["recruit"]["strain"] = strain
    return [events.menu("profession", {"strain": strain}, [])]


def pick_profession(e, prof, **a):
    ctx = e.s["script_ctx"]
    require(
        ctx and ctx.get("recruit", {}).get("strain"), "runtime_choose_a_strain_first"
    )
    ids = {m["id"] for m in e.s["roster"]}
    mid = next(i for i in range(1, e.rules["roster_cap"] + 1) if i not in ids)
    ctx["recruit"]["candidate"] = roll_member(e, ctx["recruit"]["strain"], prof, mid)
    return [
        events.state({"candidate": ctx["recruit"]["candidate"]}),
        events.menu("accept", {}, []),
    ]


def accept(e, name="Explorer", **a):
    require(
        e.s["script_ctx"] and e.s["script_ctx"].get("recruit", {}).get("candidate"),
        "runtime_no_candidate",
    )
    require(
        isinstance(name, str) and bool(name.strip()) and len(name) <= 40,
        "runtime_name_must_contain_1_40_characters",
    )
    m = e.s["script_ctx"]["recruit"]["candidate"]
    m["name"] = name.strip()
    e.s["roster"].append(m)
    e.s["script_ctx"] = None
    return [events.state({"recruited": m["id"]}), events.menu("chapter", {}, [])]


def reject(e, **a):
    e.s["script_ctx"] = None
    return [events.menu("chapter", {}, [])]
