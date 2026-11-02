# Version: 0.2.0 | 2026-11-02
"""Pure six-region frame composition (FR-UIX-001; ADR-1)."""

import textwrap
from .frame import blank_frame

REGIONS = {
    "member_panel": (0, 0, 120, 12),
    "messages": (0, 12, 60, 12),
    "menace_ranks": (60, 12, 60, 12),
    "area_map": (0, 24, 56, 16),
    "menu": (56, 24, 32, 16),
    "figures": (88, 24, 32, 16),
}


class Composer:
    def __init__(self, regs):
        self.regs = regs
        self.symbols = {
            r["name"]: r["id"] for r in regs["presentation/symbols.json"]["rows"]
        }
        self.messages = []
        self.texts = {
            r["id"]: r.get("text", r["id"])
            for p in ["text/strings.json", "text/dialogue.json", "text/runtime.json"]
            for r in regs[p]["rows"]
        }

    def compose(self, proj, pending, ctx):
        frame = blank_frame(tick=proj["tick"])

        def put(x, y, symbol, fg="parchment", flags=None):
            if 0 <= x < 120 and 0 <= y < 40:
                frame["cells"][y][x]["layers"].append(
                    dict(symbol_id=symbol, fg=fg, bg="ink", flags=set(flags or []))
                )

        def text(x, y, value, width=118, fg="parchment"):
            for i, ch in enumerate(str(value)[:width]):
                try:
                    symbol = ch.encode("cp437")[0]
                except UnicodeEncodeError:
                    symbol = ord("-") if ch in "−—–" else ord("?")
                put(x + i, y, symbol, fg)

        def border(region, title):
            x, y, w, h = REGIONS[region]
            for col in range(x, x + w):
                put(col, y, 196, "ui_frame")
            text(x + 1, y, title, w - 2, "brass")

        for region, title in [
            ("messages", "Field notes"),
            ("menace_ranks", "Menaces"),
            ("area_map", "Map"),
            ("menu", ctx.title or "Menu"),
            ("figures", "Expedition"),
        ]:
            border(region, title)
        members = {m["id"]: m for m in proj["roster"]}
        for col, mid in enumerate(proj["expedition"]["members"]):
            m = members[mid]
            x = col * 20
            for dy, value in enumerate(
                [
                    m["name"],
                    m["profession"].replace("_", " "),
                    f"HP {m['hp_cur']}/{m['hp_max']}",
                    f"MP {m['mp_cur']}/{m['mp_max']}",
                    f"L{m['level']} {m['vital']}",
                    f"XP {m['xp']}",
                    f"Credit ${m['credit']}",
                ]
            ):
                text(x + 1, dy, value, 18)
            glyphs = {"ok": "o", "injured": "!", "broken": "X", "gone": "-"}

            # Six anatomical locations in a readable surgeon's diagram.
            def area(name):
                return glyphs[m["body"][name]["sev"]]

            text(x + 5, 7, area("head"), 1)
            text(x + 3, 8, area("arm_l") + "-" + area("torso") + "-" + area("arm_r"), 5)
            text(x + 4, 9, area("leg_l") + " " + area("leg_r"), 3)
            text(x + 1, 10, proj["expedition"]["ranks"].get(mid, "middle"), 18, "ash")
        if not proj["expedition"]["members"]:
            text(2, 2, "The Cradle Plateau: The Wrath of Doctor Voss")
            text(2, 4, "Muster your expedition at the Explorers' Club chapter.")
        for event in pending:
            if event["kind"] == "MSG":
                data = event["data"]
                value = self.texts.get(data["txt_id"], data["txt_id"])
                fmt = data.get("fmt", {})
                if fmt:
                    value += "  " + ", ".join(f"{k}: {v}" for k, v in fmt.items())
                self.messages.extend(textwrap.wrap(value, 56))
            elif event["kind"] == "ERROR":
                self.messages.extend(textwrap.wrap(event["data"]["reason"], 56))
            elif event["kind"] == "STATE":
                for key in [
                    "stock",
                    "roster",
                    "pool",
                    "member",
                    "candidate",
                    "assessment",
                ]:
                    if key in event["data"]:
                        value = event["data"][key]
                        if key == "stock":
                            self.messages.extend(
                                f"{r['no']:>3} {r['name'][:22]:22} ${r['cost']} v{r['value']}"
                                + (" Unusable" if r["unusable"] else "")
                                for r in value
                            )
                        elif key == "pool":
                            self.messages.extend(
                                f"{i + 1}: {r.get('label', r['item_id']).replace('_', ' ')}"
                                for i, r in enumerate(value)
                            )
                        elif key == "roster":
                            self.messages.extend(
                                f"{r['id']}: {r['name']} / {r['profession'].replace('_', ' ')} / Post {r['resident_post']}"
                                for r in value
                            )
                        elif key in ["member", "candidate"]:
                            self.messages.append(
                                f"{value['name'] or 'Recruit'} / {value['profession'].replace('_', ' ')}"
                            )
                            self.messages.append(
                                " ".join(
                                    f"{k.upper()} {v}"
                                    for k, v in value["attrs"].items()
                                )
                            )
                            self.messages.append(
                                f"HP {value['hp_cur']}/{value['hp_max']} MP {value['mp_cur']}/{value['mp_max']} Level {value['level']}"
                            )
                            self.messages.append(
                                "Skills: "
                                + ", ".join(
                                    f"{k.replace('_', ' ')} {v}%"
                                    for k, v in value["skills"].items()
                                )
                            )
                            self.messages.append(
                                "Kit: "
                                + ", ".join(
                                    i["item_id"].replace("_", " ")
                                    for i in value["items"]
                                )
                            )
                            self.messages.append(
                                "Feats: "
                                + ", ".join(
                                    map(str, value["feats"] + value.get("rites", []))
                                )
                            )
                        else:
                            self.messages.extend(textwrap.wrap(str(value), 56))
            elif event["kind"] == "COMBAT" and "outcome" in event["data"]:
                self.messages.append(event["data"]["outcome"].title())
        self.messages = self.messages[-11:]
        for i, line in enumerate(self.messages):
            text(1, 13 + i, line, 58)
        combat = proj["combat"]
        if combat:
            for i, foe in enumerate(combat["foes"][:11]):
                status = {
                    "dead": "K",
                    "sleeping": "S",
                    "unconscious": "U",
                    "down": "D",
                }.get(foe["vital"], "")
                text(
                    61,
                    13 + i,
                    f"{foe['rank']}: {foe['name']} {status} HP {foe['hp_cur']}",
                    58,
                )
        world = proj["world"]
        map_doc = next(
            (
                d["rows"][0]
                for path, d in self.regs.files.items()
                if path.startswith("world/")
                and not path.startswith("world/scripts/")
                and d["registry"] == world["map_id"]
            ),
            None,
        )
        if map_doc:
            px, py = world["pos"]
            origin_x = max(0, min(map_doc["width"] - 54, px - 27))
            origin_y = max(0, min(map_doc["height"] - 14, py - 7))
            explored = set(
                map(tuple, world["sites"].get(world["map_id"], {}).get("explored", []))
            )
            for yy in range(14):
                for xx in range(54):
                    x, y = xx + origin_x, yy + origin_y
                    if (
                        0 <= x < map_doc["width"]
                        and 0 <= y < map_doc["height"]
                        and (
                            not world["map_id"].startswith("site") or (x, y) in explored
                        )
                    ):
                        terrain = map_doc["grid"][y][x]
                        symbol = self.symbols.get(terrain, self.symbols["wall"])
                        put(1 + xx, 25 + yy, symbol)
            for feature in map_doc.get("features", []):
                x, y = feature["pos"]
                kind = {
                    "post": "post",
                    "resthouse": "resthouse",
                    "site": "site_entrance",
                    "return": "stairs/funicular",
                }[feature["kind"]]
                if 0 <= x - origin_x < 54 and 0 <= y - origin_y < 14:
                    put(1 + x - origin_x, 25 + y - origin_y, self.symbols[kind])
            if 0 <= px - origin_x < 54 and 0 <= py - origin_y < 14:
                put(1 + px - origin_x, 25 + py - origin_y, 256)
        for i, line in enumerate(ctx.render_rows()[:15]):
            text(57, 25 + i, line, 30)
        text(89, 25, f"${proj['expedition']['treasury']}", 30, "brass")
        text(89, 26, f"Score {proj['quest_score']}/100", 30)
        text(89, 27, f"Day {proj['clock_days']}", 30)
        text(89, 28, f"{world['pos'][0]},{world['pos'][1]}", 30)
        text(89, 29, world["map_id"], 30)
        text(89, 30, f"Time lag {proj['config_echo']['time_lag']}", 30)
        text(89, 31, "Sound " + ("on" if proj["config_echo"]["sound"] else "off"), 30)
        for i, mid in enumerate(proj["expedition"]["members"]):
            put(
                90 + i * 3,
                32,
                256
                + [
                    "white_hunter",
                    "pugilist",
                    "expedition_doctor",
                    "scout",
                    "cat_burglar",
                    "antiquarian_mesmerist",
                ].index(members[mid]["profession"]),
                flags=[members[mid]["vital"]],
            )
        if combat:
            menace_symbols = {
                row["id"]: row["glyph_symbol_id"]
                for row in self.regs["registries/menaces.json"]["rows"]
            }
            for i, foe in enumerate(combat["foes"][:30]):
                put(
                    89 + i % 30,
                    34 + i // 30,
                    menace_symbols[foe["menace_id"]],
                    flags=[foe["vital"]],
                )
            for i, ally in enumerate(combat.get("allies", [])):
                put(90 + i * 3, 36, 262 + ally["id"] - 28, flags=[ally["vital"]])
        return frame
