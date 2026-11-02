# Version: 0.2.0 | 2026-11-02
"""Roster gates, residence, and automaton designation (FR-CHR-003–008)."""

from .support import require, member as get_member
from . import events


def list_members(e, **a):
    return [events.state({"roster": e.s["roster"], "automata": e.s["automata"]})]


def add_to_expedition(e, member=None, **a):
    m = get_member(e, member)
    exp = e.s["expedition"]
    require(m["resident_post"] == e.s["post_context"], e.text("not_resident"))
    require(m["id"] not in exp["members"], "runtime_already_in_expedition")
    require(len(exp["members"]) < e.rules["party_cap"], "runtime_expedition_full")
    exp["members"].append(m["id"])
    exp["ranks"][m["id"]] = "middle"
    return [events.state({"added": m["id"]})]


def drop(e, member, **a):
    m = get_member(e, member)
    exp = e.s["expedition"]
    require(member in exp["members"], "runtime_not_in_expedition")
    exp["members"].remove(member)
    exp["ranks"].pop(member, None)
    m["resident_post"] = e.s["post_context"]
    return [events.state({"dropped": member})]


def rename(e, member, name, **a):
    require(
        isinstance(name, str) and bool(name.strip()) and len(name) <= 40,
        "runtime_name_must_contain_1_40_characters",
    )
    get_member(e, member)["name"] = name.strip()
    return [events.state({"renamed": member})]


def purge(e, member, confirm=False, **a):
    require(confirm is True, "runtime_confirm_permanent_purge")
    m = get_member(e, member)
    if member in e.s["expedition"]["members"]:
        drop(e, member)
    e.s["roster"].remove(m)
    return [events.state({"purged": member})]


def designate_automaton(e, automaton=None, **a):
    ident = automaton or a.get("kind") or a.get("name")
    row = next(
        (
            m
            for m in e.s["automata"]
            if m["name"].lower() == str(ident).lower() or m["id"] == ident
        ),
        None,
    )
    require(row is not None, "runtime_unknown_automaton")
    e.s["expedition"]["automaton"] = row["id"]
    return [events.state({"automaton": row["id"]})]


def inspect(e, member=None, **a):
    return [events.state({"member": get_member(e, member)})]
