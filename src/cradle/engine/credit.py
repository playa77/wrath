# Version: 0.2.0 | 2026-11-02
"""Constrained letters of credit, checked before mutation (BR-7/OQ-9)."""

from .support import member as get_member, party, require
from . import events


def withdraw(e, member, amount, **a):
    m = get_member(e, member)
    exp = e.s["expedition"]
    require(type(amount) == int and amount >= 0, "runtime_invalid_amount")
    require(amount <= m["credit"], "runtime_insufficient_credit")
    require(exp["treasury"] + amount <= e.rules["treasury_cap"], e.text("overflow"))
    m["credit"] -= amount
    exp["treasury"] += amount
    return [events.state({"treasury": exp["treasury"]})]


def apportion(amount, shares, fee):
    net = amount - len(shares) * fee
    require(net >= 0, "runtime_deposit_does_not_cover_fees")
    total = sum(shares)
    require(total > 0, "runtime_no_deposit_shares")
    return [net * v // total for v in shares]


def deposit(e, amount, **a):
    exp = e.s["expedition"]
    members = party(e)
    require(members, e.text("no_party"))
    require(
        type(amount) == int and 0 <= amount <= exp["treasury"], "runtime_invalid_amount"
    )
    if amount == 0:
        return []
    net = amount - len(members) * e.rules["deposit_fee"]
    require(net >= 0, "runtime_deposit_does_not_cover_fees")
    shares = e.data["starting_tables"][0]["share_by_standing"]
    lots = apportion(
        amount, [shares[m["standing"]] for m in members], e.rules["deposit_fee"]
    )
    require(
        all(m["credit"] + v <= e.rules["credit_cap"] for m, v in zip(members, lots)),
        "runtime_credit_ceiling_exceeded",
    )
    for m, v in zip(members, lots):
        m["credit"] += v
    exp["treasury"] -= amount
    return [events.state({"deposited": amount, "lots": lots})]
