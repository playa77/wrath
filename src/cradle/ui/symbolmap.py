# Version: 0.2.0 | 2026-11-02
"""Entity dictionary resolution; CP437 text is presentation-only (C-6)."""

from cradle.engine.errors import ContentError


def resolve(symbol_id, states, regs):
    if symbol_id < 256:
        return symbol_id, "parchment", "ink"
    row = next(
        (r for r in regs["presentation/symbols.json"]["rows"] if r["id"] == symbol_id),
        None,
    )
    if row is None:
        raise ContentError("symbols.json", symbol_id, "unknown symbol")
    glyph, fg, bg = row["glyph"], row["fg"], row.get("bg", "ink")
    for state in sorted(states):
        variant = row.get("states", {}).get(state, {})
        glyph = variant.get("glyph", glyph)
        fg = variant.get("fg", fg)
        bg = variant.get("bg", bg)
    if isinstance(glyph, str):
        # CP437 contains Unicode symbols which Python encodes as control chars only
        # via explicit codepoint aliases. Entity rows remain Unicode in content.
        controls = {
            "☺": 1,
            "☻": 2,
            "♥": 3,
            "♦": 4,
            "♣": 5,
            "♠": 6,
            "•": 7,
            "◘": 8,
            "○": 9,
            "◙": 10,
            "♂": 11,
            "♀": 12,
            "♪": 13,
            "♫": 14,
            "☼": 15,
            "►": 16,
            "◄": 17,
            "↕": 18,
            "‼": 19,
            "¶": 20,
            "§": 21,
            "▬": 22,
            "↨": 23,
            "↑": 24,
            "↓": 25,
            "→": 26,
            "←": 27,
            "∟": 28,
            "↔": 29,
            "▲": 30,
            "▼": 31,
            "⌂": 127,
        }
        glyph = controls[glyph] if glyph in controls else glyph.encode("cp437")[0]
    return glyph, fg, bg
