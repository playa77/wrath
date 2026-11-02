# Version: 0.2.0 | 2026-11-02
"""Reproducibly transcribe normative tables; run from any working directory."""

import json
import re
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/cradle/content"
TECH = (ROOT / "docs/technical_specification.md").read_text(encoding="utf-8")
DESIGN = (ROOT / "docs/design_document.md").read_text(encoding="utf-8")


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


def table(text):
    for line in text.splitlines():
        if line.startswith("|") and not line.startswith("|---"):
            yield [v.strip() for v in line.strip("|").split("|")]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def write(path, rows, **extra):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(
            dict(
                registry=p.stem,
                schema_version=1,
                version="0.2.0",
                date="2026-11-02",
                rows=rows,
                **extra,
            ),
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main():
    strains = []
    for row in table(section(DESIGN, "| Strain | STR", "**BR-4**")):
        for offset in (0, 7):
            cells = row[offset : offset + 6]
            if cells and cells[0] and cells[1].isdigit():
                name = cells[0]
                ident = slug(name)
                kind = (
                    "charter"
                    if ident
                    in [
                        "club_stock",
                        "crag_folk",
                        "lake_folk",
                        "mesa_folk",
                        "scrub_folk",
                    ]
                    else "strange"
                )
                life = (
                    3000
                    if ident == "lake_folk"
                    else 200
                    if ident in ["crag_folk", "mesa_folk"]
                    else 80
                    if ident in ["club_stock", "scrub_folk"]
                    else 50
                )
                strains.append(
                    dict(
                        id=ident,
                        name=name,
                        kind=kind,
                        caps=dict(
                            zip(
                                ["str", "int", "dex", "con", "cha"], map(int, cells[1:])
                            )
                        ),
                        lifespan_years=life,
                        decline_marks=[0.5, 0.7, 0.9],
                        professions_allowed=["white_hunter", "cat_burglar"]
                        if kind == "strange"
                        else [],
                        fee_multiplier=1.5 if kind == "strange" else 1,
                        impression_cha_delta=-2 if kind == "strange" else 0,
                        lodging="annex" if kind == "strange" else "main",
                    )
                )
    write("registries/strains.json", strains)
    hp = {
        slug(r[0]): list(map(int, r[1:]))
        for r in table(section(DESIGN, "**BR-1 —", "CON≠10"))
        if len(r) == 16 and r[0] != "Profession" and r[1].isdigit()
    }
    mp = {
        slug(r[0]): list(map(int, r[1:]))
        for r in table(section(DESIGN, "**BR-2 —", "Intermediate levels"))
        if len(r) == 6 and r[0] != "Profession" and r[1].isdigit()
    }
    mods = dict(
        white_hunter=[2, -2, 1, 0, -1],
        pugilist=[0, 0, 1, 0, 0],
        expedition_doctor=[0, 2, 0, 0, 0],
        scout=[0, 1, 0, 0, 1],
        cat_burglar=[-2, 0, 2, 0, -1],
        antiquarian_mesmerist=[-4, 3, 2, 0, 1],
    )
    matrix = []
    block = section(TECH, "`feat_matrix.json` (OQ-5", "*Audit: union")
    for prof, body in re.findall(
        r"- \*\*(\w+)\*\* \(rate \d\):(.*?)(?=\n- \*\*|\Z)", block, re.S
    ):
        levels = [
            list(map(int, re.findall(r"\d+", xs)))
            for xs in re.findall(r"- L?\d+ (\[[^\]]+\])", body)
        ]
        # D12: close four missing offers while retaining all mandated amended rows.
        if prof == "antiquarian_mesmerist":
            levels[8].append(35)
        if prof == "cat_burglar":
            for level, feat in [(9, 38), (11, 39), (14, 40)]:
                levels[level].append(feat)
        matrix.append(dict(id=prof, levels=levels))
    write("registries/feat_matrix.json", matrix)
    professions = []
    for ident, values in hp.items():
        step = values[-1] - values[-2]
        hp20 = values + [values[-1] + step * k for k in range(1, 6)]
        anchors = dict(zip([1, 5, 10, 13, 15], mp[ident]))
        mp20 = []
        for level in range(1, 21):
            lo = max(k for k in anchors if k <= min(level, 15))
            hi = min(k for k in anchors if k >= min(level, 15))
            value = (
                anchors[lo]
                if hi == lo
                else anchors[lo]
                + (anchors[hi] - anchors[lo]) * (level - lo) / (hi - lo)
            )
            mp20.append(math.floor(value + 0.5))
        professions.append(
            dict(
                id=ident,
                name=ident.replace("_", " ").title(),
                attr_mods=mods[ident],
                hp_table=hp20,
                mp_table=mp20,
                feat_rate=2
                if ident in ["antiquarian_mesmerist", "expedition_doctor"]
                else 1,
                start_kit=["melee_1", "shield_1", "armor_1", "fire_1"],
                standing_weights=[10, 40, 35, 15],
            )
        )
    write("registries/professions.json", professions)
    skills = [
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
    starts = [
        [50, 30, 25, 20, 10, 5, 15, 5, 25],
        [45, 35, 20, 15, 5, 5, 10, 5, 10],
        [25, 15, 20, 25, 15, 10, 20, 10, 15],
        [40, 25, 35, 35, 25, 20, 30, 15, 30],
        [35, 25, 20, 30, 35, 40, 35, 45, 15],
        [20, 10, 15, 25, 20, 15, 25, 15, 15],
    ]
    prof_order = list(mods)
    write(
        "registries/starting_tables.json",
        [
            dict(
                id="rules",
                skills=skills,
                starting_skills={
                    p: dict(zip(skills, s)) for p, s in zip(prof_order, starts)
                },
                profession_skill_adds={"cat_burglar": {"marksman": 30}},
                strain_skill_adds={
                    "lake_folk": {"marksman": 15},
                    "crag_folk": {"parry": 5},
                    "mesa_folk": {"marksman": 5},
                    "scrub_folk": {"spot_trap": 5, "disarm_trap": 5},
                },
                credit_by_standing=dict(
                    zip(
                        ["urchin", "stoker", "artisan", "patrician"],
                        [250, 500, 1000, 2500],
                    )
                ),
                share_by_standing=dict(
                    zip(["urchin", "stoker", "artisan", "patrician"], [1, 2, 2, 3])
                ),
                standings=["urchin", "stoker", "artisan", "patrician"],
                strange_weights=[30, 45, 20, 5],
                starter_strains=[
                    "club_stock",
                    "club_stock",
                    "lake_folk",
                    "crag_folk",
                    "mesa_folk",
                    "scrub_folk",
                ],
                starter_professions=[
                    "white_hunter",
                    "expedition_doctor",
                    "antiquarian_mesmerist",
                    "scout",
                    "cat_burglar",
                    "pugilist",
                ],
                starter_names=["Arden", "Rowan", "Vale", "Kit", "Morgan", "Reed"],
                creation_dice=[3, 6],
                age_lifespan_fraction=0.25,
            )
        ],
    )
    write(
        "registries/xp_tables.json",
        [
            dict(
                id="rules",
                base=500,
                strain_factor={
                    s["id"]: 1.2
                    if s["kind"] == "strange" or s["id"] == "lake_folk"
                    else 1.1
                    if s["id"] in ["crag_folk", "mesa_folk"]
                    else 1
                    for s in strains
                },
                profession_factor=dict(zip(prof_order, [1, 0.9, 1.1, 1, 0.9, 1.3])),
                attribute_factor={
                    "base": 1.5,
                    "offset": 30,
                    "divisor": 100,
                    "min": 0.6,
                    "max": 1.5,
                },
            )
        ],
    )
    items = []
    item_section = section(TECH, "- **shields (1–20", "*Audit: 20+20")
    shield_names = section(item_section, "** ", ".\n- **field armor").split(", ")
    armor_names = (
        section(item_section, "**field armor (1–20;", "\n- **fire pieces")
        .split("** ", 1)[1]
        .rstrip(".")
        .split(", ")
    )
    for family, names in [("shield", shield_names), ("armor", armor_names)]:
        for n, name in enumerate(names, 1):
            name = (
                re.sub(r"\[.*?\]", "", name)
                .replace("**", "")
                .replace("`", "")
                .strip()
                .rstrip(".")
                .strip()
            )
            value = (
                n
                if family == "shield"
                else [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 10, 10, 11][
                    n - 1
                ]
            )
            elder = "Elder" in name
            items.append(
                dict(
                    id=f"{family}_{n}",
                    name=name,
                    family=family,
                    value=value,
                    cost=25 * value * (value + 1),
                    prereq={"str": math.ceil(value * 2 / 3) if elder else value},
                    flags=["elder"] if elder else [],
                    unique=False,
                )
            )
    fire_text = section(item_section, "- **fire pieces", "(The **Old Master-Bow**")
    for n, bow, rifle in re.findall(r"\n  (\d+)\. (.*?) / (.*)", fire_text):
        n = int(n)
        bow = bow.replace("**", "")
        rifle = re.sub(r"\s*\[.*", "", rifle).replace("**", "")
        if bow.startswith("+"):
            bow = "Master Longbow " + bow
        if rifle.startswith("+"):
            rifle = "Master Express " + rifle
        base = 4 + math.ceil(4 * n / 5)
        req = math.ceil(2 * base / 3) if n == 20 else base
        items.append(
            dict(
                id=f"fire_{n}",
                name=bow,
                bow_name=bow,
                rifle_name=rifle,
                family="fire",
                value=n,
                cost=25 * n * (n + 1),
                prereq={"str": req, "dex": req},
                flags=["elder"] if n == 20 else [],
                unique=False,
            )
        )
    melee = section(item_section, "- **melee (40;", "\n\n").split("** ", 1)[1]
    for n, piece in enumerate(melee.split(", "), 1):
        clean = (
            re.sub(r"\[.*?\]", "", piece)
            .replace("**", "")
            .replace("`", "")
            .strip()
            .rstrip(".")
            .strip()
        )
        name, value = clean.rsplit(" ", 1)
        value = int(value)
        elder = "Elder" in name
        items.append(
            dict(
                id=f"melee_{n}",
                name=name,
                family="weapon",
                value=value,
                cost=25 * value * (value + 1),
                prereq={
                    "twostr_plus_dex": math.ceil((10 + value) * 2 / 3)
                    if elder
                    else 10 + value
                },
                flags=["elder"] if elder else [],
                unique=False,
            )
        )
    write("registries/items.json", items)
    tonics = []
    for n in range(1, 11):
        tonics += [
            dict(
                id=f"radium_tonic_{n}",
                name=f"Radium Tonic {n}",
                family="tonic",
                hp=n * n,
                cure_tier=1 if n <= 3 else 2 if n <= 6 else 3 if n <= 9 else 4,
                cost=50 * n * n,
                value=n,
                prereq={},
                flags=[],
            ),
            dict(
                id=f"nerve_tonic_{n}",
                name=f"Nerve Tonic {n}",
                family="tonic",
                mp=3 * n,
                cost=30 * n * n,
                value=n,
                prereq={},
                flags=[],
            ),
        ]
    write("registries/tonics.json", tonics)
    folios = []
    for r in table(section(TECH, "| # | Title | Payload topic", "Full payload texts")):
        if r[0] not in ["#"]:
            folios.append(
                dict(
                    id="folio_" + r[0],
                    name=r[1],
                    family="folio",
                    payload=r[0],
                    location=r[3],
                    cost=50,
                    value=0,
                    prereq={},
                    flags=[],
                    sealed=r[0] == "XVI",
                    read_msg="The ink has long since run to ruin."
                    if r[0] == "XVI"
                    else "",
                )
            )
    folios += [
        dict(
            id=f"club_gazette_{n}",
            name=f"Club Gazette {n}",
            family="folio",
            cost=25,
            value=0,
            prereq={},
            flags=[],
            text="Plateau society pages: arrivals, departures, and expedition notices.",
        )
        for n in range(1929, 1933)
    ]
    write("registries/folio_items.json", folios)
    valuables = []
    for ident in [
        "sun_key",
        "drowned_key",
        "sun_gem",
        "obsidian_urn",
        "crystal_resonator",
        "foul_phial",
        "sweet_phial",
        "old_master_bow",
    ]:
        valuables.append(
            dict(
                id=ident,
                name=ident.replace("_", " ").title(),
                family="fire" if ident == "old_master_bow" else "valuable",
                bound=ident == "crystal_resonator",
                unique=True,
                cost=0,
                value=19 if ident == "old_master_bow" else 0,
                prereq={"str": 20, "dex": 20} if ident == "old_master_bow" else {},
                flags=[],
            )
        )
    val_text = section(TECH, "(name, $): ", "\n\n### 5.4")
    for name, value in re.findall(r"([a-z][a-z -]+?) ([\d,]+)(?= \(|, |\.)", val_text):
        valuables.append(
            dict(
                id=slug(name.strip()),
                name=name.strip().title(),
                family="valuable",
                cost=int(value.replace(",", "")),
                value=0,
                prereq={},
                flags=[],
                unique=False,
            )
        )
    write("registries/valuables.json", valuables)
    feats = []
    for row in table(section(DESIGN, "| # | Feat | MP", "### 5.5 Equipment")):
        if not re.match(r"\d", row[0]):
            continue
        nums = re.findall(r"\d+", row[0])
        ids = range(int(nums[0]), int(nums[-1]) + 1)
        for tier, ident in enumerate(ids, 1):
            name = row[1].replace("1–4", str(tier)).replace("(elder rite)", "").strip()
            mpv = tier if row[2] == "1–4" else int(row[2]) if row[2].isdigit() else 0
            feats.append(
                dict(
                    id=ident,
                    name=name,
                    mp=mpv,
                    domain=row[3].lower(),
                    **{"class": row[4].lower()},
                    effect={"notes": row[5]},
                    vacant=ident == 53,
                )
            )
    for f in feats:
        n = f["id"]
        for start, maxima in [
            (1, [9, 27, 57, 99]),
            (5, [10, 30, 60, 100]),
            (9, [7, 15, 31, 66]),
            (33, [5, 11, 41, 81]),
            (37, [12, 35, 70, 120]),
        ]:
            if start <= n < start + 4:
                f["effect"]["dice"] = "1d" + str(maxima[n - start])
        if 1 <= n <= 4:
            f["effect"]["cure_tier"] = n
        if n == 13:
            f["effect"].update(accuracy_pct=50, fire_value=15)
    write("registries/feats.json", feats)
    menaces = []
    for row in table(section(TECH, "**Band 1 (low,", "*Audit: rows = 78")):
        if not row[0].isdigit():
            continue
        n = int(row[0])
        notes = row[8]
        tier = row[2]
        cast = re.search(r"feats\[([^\]]+)\] casts (\d+)", notes)
        flags = [
            f
            for f, condition in [
                ("M", n in [25, 26, 39, 54, 55, 76, 77, 78]),
                ("C", bool(cast)),
                ("unique", n in [58, 59, 60, 61, 72, 73, 74, 75, 76]),
                ("tall", "tall" in notes),
            ]
            if condition
        ]
        menaces.append(
            dict(
                id=n,
                name=row[1],
                tier=tier,
                disp=row[3],
                pack_max=int(row[4]),
                hp=int(row[5]),
                dmg=row[6],
                xp=int(row[7]),
                band_min=1
                if n <= 10
                else 2
                if n <= 30 or n >= 77
                else 3
                if n <= 50
                else 4,
                flags=flags,
                feats=list(map(int, re.findall(r"\d+", cast[1]))) if cast else [],
                cast_budget=int(cast[2]) if cast else 0,
                treasure=(re.search(r"t[1-8]", notes) or ["t1"])[0],
            )
        )
    # Map explicit symbol table order to menace rows (D03).
    symbols = []
    for row in table(section(TECH, "**Members:**", "*(IDs unique")):
        if not row[0].isdigit():
            continue
        n = int(row[0])
        glyph = row[2]
        fg = row[3].split(" ")[0] or "hide"
        states = {}
        if n < 262:
            states = {
                "sleeping": {"fg": "sleep"},
                "down": {"fg": "warn"},
                "unconscious": {"fg": "bad"},
                "dead": {"glyph": "%", "fg": "gore"},
                "hollowed": {"fg": "hollow"},
            }
        if len(row) > 4 and "+M" in row[4]:
            states["mummified"] = {"fg": "ash"}
        symbols.append(
            dict(id=n, name=row[1], glyph=glyph, fg=fg, bg="ink", states=states)
        )
    menace_symbols = [s for s in symbols if s["id"] >= 325]
    for row, sym in zip(menaces, menace_symbols):
        row["glyph_symbol_id"] = sym["id"]
    write("registries/menaces.json", menaces)
    write("presentation/symbols.json", symbols)
    colors = []
    for row in table(section(TECH, "| token | RGB", "#### 5.10.2")):
        for i in (0, 2):
            if row[i] and row[i + 1].startswith("#"):
                colors.append(
                    dict(
                        id=row[i],
                        rgb=[int(row[i + 1][k : k + 2], 16) for k in [1, 3, 5]],
                    )
                )
    colors.append(dict(id="badlands", rgb=[74, 68, 64]))
    write("text/color_tokens.json", colors)


if __name__ == "__main__":
    main()
