# Version: 0.1.0 | 2026-11-02
"""Spec §6.2: pure event constructors; the dispatch owner stamps engine ticks."""

from typing import Literal, TypedDict
from .errors import DomainError

EventKind = Literal[
    "MSG",
    "MENU",
    "STATE",
    "MAP",
    "COMBAT",
    "SFX_FLAG",
    "SAVE_WRITTEN",
    "ENDING",
    "ERROR",
]


class Event(TypedDict):
    kind: EventKind
    tick: int
    data: dict


def msg(txt_id: str, *, tick: int = 0, **fmt) -> Event:
    return {"kind": "MSG", "tick": tick, "data": {"txt_id": txt_id, "fmt": fmt}}


def menu(menu_id: str, ctx: dict, slots: list, *, tick: int = 0) -> Event:
    return {
        "kind": "MENU",
        "tick": tick,
        "data": {"menu_id": menu_id, "ctx": ctx.copy(), "slots": slots.copy()},
    }


def state(delta: dict, *, tick: int = 0) -> Event:
    return {"kind": "STATE", "tick": tick, "data": delta.copy()}


def map_update(cells: list, *, tick: int = 0) -> Event:
    return {"kind": "MAP", "tick": tick, "data": {"cells": cells.copy()}}


def combat(rec: dict, *, tick: int = 0) -> Event:
    return {"kind": "COMBAT", "tick": tick, "data": rec.copy()}


def sfx_flag(name: str, *, tick: int = 0) -> Event:
    return {"kind": "SFX_FLAG", "tick": tick, "data": {"name": name}}


def save_written(path: str, *, tick: int = 0) -> Event:
    return {"kind": "SAVE_WRITTEN", "tick": tick, "data": {"path": path}}


def ending(kind: str, *, tick: int = 0) -> Event:
    return {"kind": "ENDING", "tick": tick, "data": {"kind": kind}}


def error(e: DomainError, *, tick: int = 0) -> Event:
    return {"kind": "ERROR", "tick": tick, "data": {"verb": e.verb, "reason": e.reason}}


def stamp(pending: list[Event], tick: int) -> list[Event]:
    """Core calls once per dispatch; no hidden global counter or wall clock."""
    return [{**event, "tick": tick} for event in pending]
