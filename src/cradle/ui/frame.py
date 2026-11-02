# Version: 0.1.0 | 2026-11-02
"""Spec §6.3: renderer-independent ordered cell stacks."""
from typing import TypedDict


class Layer(TypedDict):
    symbol_id: int
    fg: str
    bg: str
    flags: set[str]


class Cell(TypedDict):
    layers: list[Layer]


class Frame(TypedDict):
    w: int
    h: int
    cells: list[list[Cell]]
    tick: int


def blank_frame(*, tick: int = 0) -> Frame:
    return {"w": 120, "h": 40, "tick": tick,
            "cells": [[{"layers": []} for _ in range(120)] for _ in range(40)]}
