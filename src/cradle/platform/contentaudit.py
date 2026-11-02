# Version: 0.2.0 | 2026-11-02
"""Full-pack counts, anchor values, reference integrity and reachability."""

from collections import deque
from cradle.engine.errors import ContentError
from cradle.engine.commands import VERBS

COUNTS = {
    "strains": 15,
    "professions": 6,
    "items": 101,
    "tonics": 20,
    "folio_items": 20,
    "valuables": 41,
    "feats": 58,
    "menaces": 78,
    "posts": 17,
    "symbols": 112,
    "folios": 15,
}


def audit(regs):
    def fail(file, row, why):
        raise ContentError(file, row, why)

    data = {path: doc for path, doc in regs.files.items()}

    def registry(name):
        docs = [
            doc
            for path, doc in data.items()
            if doc["registry"] == name and not path.startswith("world/scripts/")
        ]
        if len(docs) != 1:
            fail(name, "header", "required registry missing or ambiguous")
        return docs[0]["rows"]

    for name, count in COUNTS.items():
        if len(registry(name)) != count:
            fail(name, "rows", f"expected {count} rows")
    items = {
        r["id"]: r
        for name in ["items", "tonics", "folio_items", "valuables"]
        for r in registry(name)
    }
    if len(items) != 182:
        fail("items", "rows", "expected 182 unique item identities (D01)")
    symbols = {r["id"]: r for r in registry("symbols")}
    colors = {r["id"] for r in registry("color_tokens")}
    menaces = {r["id"]: r for r in registry("menaces")}
    feats = {r["id"]: r for r in registry("feats")}
    for ident, row in symbols.items():
        if row["fg"] not in colors or row["bg"] not in colors:
            fail("symbols", ident, "unknown color token")
    for ident, row in menaces.items():
        if row["glyph_symbol_id"] not in symbols or row["xp"] > 65535:
            fail("menaces", ident, "invalid symbol or XP")
        if any(n not in feats for n in row["feats"]):
            fail("menaces", ident, "unknown feat")
    actual = {n for n, r in menaces.items() if "M" in r["flags"]}
    if actual != {25, 26, 39, 54, 55, 76, 77, 78}:
        fail("menaces", "flags", "mummified set differs from anchor")
    offers = {
        n for p in registry("feat_matrix") for level in p["levels"] for n in level
    }
    if offers != (set(range(1, 53)) | {54, 55, 56}):
        fail("feat_matrix", "rows", "learnable coverage incomplete")
    if not feats[53]["vacant"] or feats[56]["mp"] != 2:
        fail("feats", 53, "vacancy/trance anchor mismatch")
    if items["armor_20"]["value"] != 11 or items["melee_41"]["value"] != 25:
        fail("items", "anchor", "elder value mismatch")
    for row in registry("menus"):
        for option in row["options"]:
            if option["verb"] not in VERBS:
                fail("menus", row["id"], "unregistered verb")
    allowed = {
        "msg",
        "menu",
        "combat",
        "give_item",
        "take_item",
        "set_flag",
        "damage",
        "mp_zero",
        "transport",
        "award_con",
        "award_xp",
        "journal_hint",
        "infamy",
        "ending",
    }

    def actions(file, rows):
        for a in rows:
            if a["verb"] not in allowed:
                fail(file, a["verb"], "unknown DSL action")
            if (
                a["verb"] in ["give_item", "take_item"]
                and a.get("id") not in items
                and not a.get("treasure")
            ):
                fail(file, a.get("id"), "unknown item")
            if a["verb"] == "combat" and any(n not in menaces for n in a["foes"]):
                fail(file, "combat", "unknown menace")
            if a.get("on_win"):
                actions(file, a["on_win"])
            for option in a.get("options", []):
                actions(file, option["then"])

    for n in range(1, 12):
        site = f"site{n:02}"
        path = f"world/sites/{site}.json"
        scripts = f"world/scripts/{site}.json"
        if path not in data or scripts not in data:
            fail(site, "header", "missing map/scripts")
        doc = data[path]["rows"][0]
        grid = doc["grid"]
        w, h = doc["width"], doc["height"]
        if (w, h) != (30, 24) or len(grid) != h or any(len(row) != w for row in grid):
            fail(path, "grid", "invalid dimensions")
        seen = {tuple(doc["entry"])}
        todo = deque(seen)
        while todo:
            x, y = todo.popleft()
            for xx, yy in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                if (
                    0 <= xx < w
                    and 0 <= yy < h
                    and grid[yy][xx] not in ["wall", "solid"]
                    and (xx, yy) not in seen
                ):
                    seen.add((xx, yy))
                    todo.append((xx, yy))
        for row in data[scripts]["rows"]:
            if tuple(row["at"]) not in seen:
                fail(scripts, row["id"], "script square unreachable")
            actions(scripts, row["then"])
    for name, w, h in [
        ("province", 75, 50),
        ("ziggurat_sun", 18, 9),
        ("ziggurat_drowned", 18, 9),
        ("deeps", 30, 15),
    ]:
        row = registry(name)[0]
        if (
            (row["width"], row["height"]) != (w, h)
            or len(row["grid"]) != h
            or any(len(r) != w for r in row["grid"])
        ):
            fail(name, "grid", "dimensions mismatch")
