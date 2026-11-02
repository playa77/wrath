# Version: 0.2.0 | 2026-11-02
"""Domain lookups and guard helpers; no infrastructure or display knowledge."""

from collections.abc import Mapping
from copy import deepcopy
from .errors import DomainError
from . import events


def thaw(value):
    if isinstance(value, Mapping):
        return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw(v) for v in value]
    if isinstance(value, set):
        return [thaw(v) for v in sorted(value)]
    return deepcopy(value)


def rows(e, name):
    return e.data[name]


def member(e, mid=None, *, living=False):
    if mid is None:
        mid = e.s["expedition"]["members"][0] if e.s["expedition"]["members"] else None
    m = next((m for m in e.s["roster"] if m["id"] == mid), None)
    require(m is not None, "runtime_unknown_member")
    if e.s["phase"] in ["trail", "site", "encounter", "combat"]:
        require(
            m["id"] in e.s["expedition"]["members"],
            "runtime_member_is_not_in_the_expedition",
        )
    if living:
        require(m["vital"] != "dead", e.text("dead"))
    return m


def party(e, living=False):
    ids = e.s["expedition"]["members"]
    return [
        m
        for m in e.s["roster"]
        if m["id"] in ids and (not living or m["vital"] != "dead")
    ]


def require(ok, reason):
    if not ok:
        raise DomainError("", reason)


def emit(text, **fmt):
    return [events.msg(text, **fmt)]


def item_instance(e, ident, skin=None):
    row = e.items[ident]
    return dict(
        item_id=ident,
        skin=skin if row["family"] == "fire" else None,
        bound=row.get("bound", False),
    )


def held(e, ident):
    return any(i["item_id"] == ident for m in party(e) for i in m["items"]) or any(
        i["item_id"] == ident for i in e.s["expedition"]["found_items"]
    )


def credit_money(e, amount):
    exp = e.s["expedition"]
    cap = e.rules["treasury_cap"]
    overflow = max(0, exp["treasury"] + amount - cap)
    exp["treasury"] = min(cap, exp["treasury"] + amount)
    return emit("forfeit", amount=overflow) if overflow else []
