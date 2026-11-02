# Version: 0.2.0 | 2026-11-02
"""Compile geography and declarative site scripts from Doc 2 §5.6–5.8."""

from build_content import write


def rect(grid, box, value):
    x1, y1, x2, y2 = box
    for y in range(max(0, y1), min(len(grid), y2 + 1)):
        for x in range(max(0, x1), min(len(grid[0]), x2 + 1)):
            grid[y][x] = value


def line(grid, a, b, value="floor"):
    x, y = a
    tx, ty = b
    # Bresenham keeps river and corridors continuous without diagonal holes.
    while (x, y) != (tx, ty):
        grid[y][x] = value
        if x != tx:
            x += 1 if x < tx else -1
        elif y != ty:
            y += 1 if y < ty else -1
    grid[y][x] = value


def action(verb, **kw):
    return dict(verb=verb, **kw)


def msg(text):
    return action("msg", text=text)


def flag(name, value=True):
    return action("set_flag", name=name, value=value)


def give(item):
    return action("give_item", id=item)


def menu(ident, labels):
    return action(
        "menu",
        id=ident,
        options=[dict(label=label, then=actions) for label, actions in labels],
    )


def combat(foes, **kw):
    return action("combat", foes=foes, **kw)


def transport(map_id, x, y):
    return action("transport", map_id=map_id, pos=[x, y])


def main():
    grid = [["trail"] * 75 for _ in range(50)]
    for terrain, boxes in [
        (
            "escarpment",
            [(8, 4, 20, 8), (4, 8, 12, 16), (62, 2, 72, 6), (66, 6, 70, 10)],
        ),
        ("swamp", [(55, 40, 68, 48), (10, 36, 20, 42), (44, 34, 52, 40)]),
        ("badlands", [(30, 2, 44, 6), (12, 18, 18, 26), (56, 28, 64, 34)]),
    ]:
        for box in boxes:
            rect(grid, box, terrain)
    river = [
        (20, 18),
        (24, 20),
        (28, 24),
        (34, 28),
        (42, 32),
        (50, 36),
        (56, 40),
        (60, 44),
    ]
    for a, b in zip(river, river[1:]):
        line(grid, a, b, "river")
    rect(grid, (56, 20, 62, 24), "water")
    for x in range(75):
        grid[0][x] = grid[-1][x] = "escarpment"
    for y in range(50):
        grid[y][0] = grid[y][-1] = "escarpment"
    post_names = [
        "Terminus",
        "Xavier's Drift",
        "Salt Landing",
        "Flagler Station",
        "Pendry's Ferry",
        "Lansing Post",
        "Rockfell Camp",
        "Scandia Port",
        "Delta Post",
        "Schatika Post",
        "Tamarisk Mission",
        "Serein Mission",
        "Tiernan's Landing",
        "Anvil Camp",
    ]
    post_pos = [
        (37, 24),
        (25, 45),
        (8, 40),
        (55, 8),
        (20, 18),
        (65, 15),
        (10, 12),
        (30, 8),
        (60, 45),
        (50, 30),
        (52, 20),
        (45, 40),
        (70, 35),
        (15, 35),
    ]
    posts = [
        dict(id=i + 1, name=n, pos=list(p), kind="post", map_id="province")
        for i, (n, p) in enumerate(zip(post_names, post_pos))
    ]
    rests = [
        dict(id="rest" + str(i + 1), name=n, pos=list(p), kind="resthouse")
        for i, (n, p) in enumerate(
            zip(
                [
                    "Deadfall Rest",
                    "Badlands Rest",
                    "Crown Rest",
                    "Campfire Rest",
                    "Portage House",
                    "Royal Rest",
                    "Mirage Rest",
                    "Jolly Rest",
                ],
                [
                    (18, 26),
                    (14, 44),
                    (33, 14),
                    (28, 33),
                    (44, 20),
                    (62, 25),
                    (48, 38),
                    (40, 10),
                ],
            )
        )
    ]
    sites = [
        dict(id=f"site{i:02}", name=n, pos=list(p), kind="site")
        for i, n, p in [
            (1, "The Map Room", (34, 30)),
            (2, "The Halls of the Colossi", (36, 42)),
            (3, "The Crag-Folk Burial Vaults", (8, 20)),
            (4, "The Hidden Enclave", (12, 32)),
            (5, "The Funicular Station", (58, 22)),
            (8, "Lord Wood's War-Camp", (48, 6)),
            (10, "The Hermit's Shack", (68, 8)),
            (11, "The Drake Hollows", (24, 38)),
        ]
    ]
    # D15: the Station coordinate lies inside the lake rectangle. Its approach
    # causeway keeps the mandatory site reachable while open water stays blocked.
    line(grid, (55, 22), (58, 22), "trail")
    for f in posts + rests + sites:
        grid[f["pos"][1]][f["pos"][0]] = "trail"
    write(
        "world/province.json",
        [
            dict(
                id="province",
                name="The Cradle Plateau",
                width=75,
                height=50,
                grid=grid,
                features=posts + rests + sites,
            )
        ],
    )
    planar = []
    for ident, name, num, site in [
        ("ziggurat_sun", "Sun-Terrace Station", 15, "site06"),
        ("ziggurat_drowned", "Lake-Bottom Post", 16, "site07"),
        ("deeps", "Fumarole Camp", 17, "site09"),
    ]:
        w, h = (30, 15) if ident == "deeps" else (18, 9)
        g = [["floor"] * w for _ in range(h)]
        pos = [4, 7] if ident == "deeps" else [9, 6]
        post = dict(id=num, name=name, pos=pos, kind="post", map_id=ident)
        planar.append(post)
        features = [
            post,
            dict(
                id=site,
                name={
                    "site06": "Sun citadel",
                    "site07": "Drowned citadel",
                    "site09": "Basalt Fastness",
                }[site],
                pos=[26, 7] if ident == "deeps" else [9, 1],
                kind="site",
            ),
        ]
        if ident == "deeps":
            for box in [
                (8, 5, 11, 5),
                (8, 10, 11, 10),
                (13, 3, 13, 14),
                (16, 2, 18, 4),
                (16, 11, 18, 13),
                (20, 6, 20, 8),
                (22, 2, 25, 3),
                (22, 12, 25, 13),
            ]:
                rect(g, box, "lava")
        else:
            features.append(
                dict(id="return", name="Funicular plaza", kind="return", pos=[9, 8])
            )
        write(
            "world/" + ident + ".json",
            [
                dict(
                    id=ident,
                    name=ident.replace("_", " ").title(),
                    width=w,
                    height=h,
                    grid=g,
                    features=features,
                )
            ],
        )
    write("registries/posts.json", posts + planar)
    pools = dict(
        trail=[6, 7, 8, 9, 11, 48],
        badlands=[5, 6, 7, 13, 18, 19, 33],
        swamp=[1, 3, 14, 23, 24, 28, 29, 30],
        escarpment=[19, 21, 31, 43, 46, 47, 50, 61],
        river=[],
        floor=[62, 63, 64, 65, 66, 67, 68, 69, 70, 71],
    )
    write(
        "world/encounters_tables.json",
        [
            dict(id=k, denominator=d, pool=pools[k])
            for k, d in [
                ("trail", 12),
                ("badlands", 10),
                ("swamp", 8),
                ("escarpment", 6),
                ("river", 0),
                ("floor", 12),
            ]
        ],
        treasure=[
            dict(id="t" + str(i + 1), dollars=list(d), chance=c, value=list(v))
            for i, (d, c, v) in enumerate(
                zip(
                    [
                        (5, 40),
                        (20, 120),
                        (50, 250),
                        (100, 500),
                        (200, 900),
                        (400, 1600),
                        (800, 4000),
                        (1500, 8000),
                    ],
                    [10, 15, 20, 25, 30, 35, 40, 50],
                    [
                        (1, 3),
                        (2, 6),
                        (4, 9),
                        (6, 12),
                        (8, 15),
                        (10, 18),
                        (12, 20),
                        (15, 25),
                    ],
                )
            )
        ],
    )
    for n in range(1, 12):
        build_site(n)


def build_site(n):
    ident = f"site{n:02}"
    grid = [["wall"] * 30 for _ in range(24)]
    scripts = []
    sets = []
    traps = []
    doors = []
    panels = []
    entry = (
        [15, 22]
        if n in [1, 6, 7]
        else [15, 1]
        if n in [2, 3, 11]
        else [2, 12]
        if n == 9
        else [15, 23]
    )
    pools = {
        1: [6, 25, 77, 78],
        2: [8, 20, 25, 22],
        3: [25, 26, 36],
        4: [13, 19],
        5: [27, 39],
        6: [],
        7: [54, 55, 56],
        8: [48, 50, 52],
        9: [39, 52, 53],
        10: [],
        11: [10, 21, 31],
    }
    names = [
        "The Map Room",
        "The Halls of the Colossi",
        "The Crag-Folk Burial Vaults",
        "The Hidden Enclave",
        "The Funicular Station",
        "Sun-Ziggurat Citadel",
        "Drowned Ziggurat Citadel",
        "Lord Wood's War-Camp",
        "Voss's Basalt Fastness",
        "The Hermit's Shack",
        "The Drake Hollows",
    ]

    def square(x, y, actions, **gates):
        scripts.append(
            dict(
                id=f"{ident}_{x}_{y}_{len(scripts)}",
                at=[x, y],
                on="enter",
                **{"if": gates},
                then=actions,
            )
        )

    def stash(x, y, items, treasure=None):
        square(
            x,
            y,
            [give(i) for i in items]
            + ([action("give_item", treasure=treasure)] if treasure else []),
            once=f"{ident}.stash.{x}.{y}",
        )

    def set_at(x, y, foes, **kw):
        sid = f"{ident}.set{len(sets) + 1}"
        sets.append(dict(id=sid, at=[x, y], foes=foes, **kw))
        square(x, y, [combat(foes, set_id=sid, **kw)], dead_set=sid)

    def trap(x, y, kind):
        traps.append(dict(at=[x, y], kind=kind))

    if n == 1:
        rooms = [
            (13, 20, 17, 23),
            (22, 16, 28, 20),
            (22, 10, 28, 14),
            (22, 4, 27, 8),
            (16, 12, 19, 15),
            (16, 6, 19, 9),
            (8, 14, 13, 18),
            (1, 2, 7, 21),
            (1, 1, 4, 3),
            (20, 2, 21, 5),
        ]
        doors = [dict(at=[14, 16], kind="door"), dict(at=[4, 3], kind="locked")]
        panels = [[8, 16], [19, 3]]
        trap(12, 18, "dart")
        trap(5, 5, "fume")
        square(6, 19, [msg("Warning — Danger lies beyond.")])
        square(24, 6, [msg("Port and cheese wait on the curator's table.")])
        square(17, 13, [msg("A waste-paper pit.")])
        square(17, 7, [msg("A weapon cupboard.")])
        stash(17, 8, ["melee_7", "melee_11"])
        square(10, 16, [action("menu", id="filmon", special="filmon")])
        square(15, 15, [action("menu", id="shrine", special="shrine")])
        square(
            2,
            2,
            [
                menu(
                    "resonator",
                    [
                        ("Take", [give("crystal_resonator"), msg("DLG-020")]),
                        ("Leave", []),
                    ],
                )
            ],
            once="site01.resonator",
        )
        for x, y, f in [
            (5, 18, [6, 6]),
            (4, 12, [26, 78, 78]),
            (4, 7, [77, 77, 27]),
            (3, 4, [32, 33]),
        ]:
            set_at(x, y, f)
        stash(21, 3, ["diamond"], "t4")
        stash(26, 18, ["folio_II"])
        stash(25, 12, ["folio_III"])
    elif n == 2:
        rooms = [
            (4, 2, 26, 16),
            (24, 3, 28, 8),
            (11, 6, 15, 10),
            (1, 16, 5, 22),
            (23, 9, 27, 13),
            (9, 13, 11, 15),
        ] + [(x, 18, min(29, x + 3), 22) for x in [3, 8, 13, 18, 23, 28]]
        doors = [dict(at=[15, 17], kind="door"), dict(at=[10, 14], kind="unpickable")]
        panels = [[15, 22]]
        for x, y, k in [(20, 6, "pitch"), (9, 9, "slab"), (24, 18, "spear")]:
            trap(x, y, k)
        square(
            15, 4, [transport(ident, 15, 20), flag("chute_fallen")], once="chute_fallen"
        )
        square(25, 20, [msg("KILMOR WAS HERE.")])
        square(
            25,
            21,
            [
                msg("Kilmor's starved body lies beside a blood-written journal."),
                give("folio_I"),
                flag("kilmor_found"),
            ],
            once="kilmor_found",
        )
        square(25, 21, [msg("Only a bloodstain.")], flag="kilmor_found")
        for x in [5, 13]:
            square(x, 20, [msg("Only bones remain.")])
        square(
            9,
            20,
            [
                msg("A starved prisoner is freed. Search for Kilmor in the pens."),
                flag("journal_hint"),
            ],
        )
        square(
            26,
            5,
            [
                menu(
                    "levers",
                    [
                        (
                            str(i),
                            [combat([44])]
                            if i == 3
                            else [flag("beasts_dead"), msg("Both penned horrors die.")]
                            if i == 4
                            else [msg("Nothing moves.")],
                        )
                        for i in range(1, 7)
                    ]
                    + [("Leave", [])],
                )
            ],
        )
        square(
            13,
            8,
            [
                menu(
                    "wrestle",
                    [
                        (
                            "Accept",
                            [
                                action("mp_zero"),
                                combat(
                                    [59],
                                    wrestle=True,
                                    on_win=[
                                        action("award_con", amount=1),
                                        flag("wrestled"),
                                    ],
                                ),
                            ],
                        ),
                        ("Refuse", []),
                    ],
                )
            ],
            not_flag="wrestled",
        )
        square(15, 9, [msg("…no devices, no draughts, no mesmerism — bare hands.")])
        square(
            3, 19, [msg("The Sun-Key glows; the dark force yields.")], item="sun_key"
        )
        square(
            3,
            19,
            [msg("Dark force snuffs the lights."), transport(ident, 4, 19)],
            not_item="sun_key",
        )
        stash(3, 21, ["drowned_key"])
        scripts[-1]["if"]["item"] = "sun_key"
        square(
            25,
            11,
            [
                menu(
                    "cache",
                    [
                        ("Blast", [give("smoky_gem"), give("smoky_gem")]),
                        (
                            "Ease",
                            [
                                action("damage", dice=[1, 12]),
                                give("fine_gem"),
                                give("fine_gem"),
                            ],
                        ),
                    ],
                )
            ],
            once="site02.cache",
        )
        square(7, 3, [msg("Avoid the Colossi pens until you are strong enough.")])
        square(
            17,
            3,
            [msg("Find the prison block — something powerful hangs in the air there.")],
        )
        stash(15, 2, [], "t5")
    elif n == 3:
        rooms = [(8, 4, 22, 10), (4, 12, 10, 18), (20, 12, 26, 18), (19, 17, 21, 19)]
        trap(8, 12, "fume")
        trap(20, 12, "deadfall")
        square(15, 2, [msg("DLG-030")], flag="kilmor_found")
        guests = [
            (9, 5, "Lord Wood and Lady Katherine"),
            (11, 5, "Prelate Turak"),
            (13, 5, "Princess Charista and Prince Lefrod"),
            (17, 5, "High Chief Argon"),
            (19, 5, "Pelzer the master bowyer"),
            (21, 5, "Scrub-Folk envoys"),
            (9, 6, "Kilmor's family"),
            (21, 6, "His comrades"),
        ]
        for x, y, name in guests:
            square(x, y, [msg(name)], not_flag="funeral_done")
            square(x, y, [msg("Charred bodies and empty chairs.")], flag="funeral_done")
        square(
            15,
            6,
            [msg(f"DLG-{i:03}") for i in range(31, 36)] + [flag("funeral_done")],
            flag="kilmor_found",
            once="funeral_done",
        )
        square(15, 4, [msg("Ashes.")], flag="funeral_done")
        square(
            20,
            18,
            [msg("The sarcophagus is empty. The lock will not yield to any pick.")],
        )
        doors = [dict(at=[20, 18], kind="unpickable")]
        set_at(4, 14, [36, 36])
        set_at(24, 14, [37, 36])
        stash(12, 18, [], "t3")
    elif n == 4:
        rooms = [
            (10, 4, 20, 9),
            (4, 12, 8, 16),
            (24, 13, 27, 17),
            (18, 13, 22, 16),
            (22, 2, 27, 7),
            (4, 18, 8, 22),
        ]
        doors = [
            dict(at=[15, 22], kind="enclave"),
            dict(at=[20, 20], kind="unpickable"),
        ]
        trap(14, 14, "spear")
        trap(22, 10, "dart")
        square(15, 6, [msg("DLG-042")])
        square(6, 14, [action("menu", id="brood", special="brood")])
        stash(25, 14, ["foul_phial"])
        stash(25, 16, ["sweet_phial"])
        square(20, 14, [msg("Records of the master bowyers.")])
        stash(24, 4, ["folio_VI"])
        square(26, 5, [action("menu", id="mesmerist", special="mesmerist")])
        square(10, 20, [msg("DLG-048")])
        set_at(6, 20, [58])
        stash(5, 21, ["fire_18"], "t5")
    elif n == 5:
        rooms = [
            (4, 8, 26, 18),
            (4, 4, 26, 6),
            (20, 2, 24, 8),
            (4, 2, 8, 6),
            (2, 10, 6, 16),
            (24, 10, 28, 16),
        ]
        square(10, 18, [msg("DLG-050")])
        square(12, 18, [msg("Monday A7+ · Tuesday B7− · Wednesday C2+")])
        for x, title in zip(
            range(4, 27, 3),
            [
                "Light",
                "Chaos",
                "Harmony",
                "Beasts",
                "First Age of Man",
                "Second Age of Man",
                "Destruction",
                "the Present Age",
            ],
        ):
            square(x, 4, [msg("Dossier: " + title)])
        stash(23, 3, ["folio_VII"])
        stash(21, 3, ["folio_XII"])
        square(6, 4, [msg("A cracked ceiling-lens illuminates a glowing key.")])
        stash(6, 3, ["sun_key"])
        square(22, 4, [action("menu", id="chronos", special="chronos")])
        square(21, 6, [action("menu", id="drake", special="drake")])
        square(4, 13, [action("menu", id="console", special="console")])
        square(26, 13, [action("menu", id="lever", special="funicular")])
    elif n in [6, 7]:
        rooms = [
            (13, 20, 17, 23),
            (3, 2, 26, 4),
            (8, 8, 22, 13),
            (5, 15, 24, 18),
            (13, 5, 17, 7),
        ]
        doors = [dict(at=[15, 21], kind="sun" if n == 6 else "drowned")]
        scorch = [(12, 8), (18, 8), (15, 6), (15, 18), (7, 16), (23, 16)]
        for x, y in scorch:
            square(
                x,
                y,
                [
                    action("damage", dice=[2, 8] if n == 6 else [0, 80]),
                    msg("A lens-ray scorches the column."),
                ],
            )
        if n == 6:
            for x, y in [(10, 10), (20, 10)]:
                square(x, y, [action("damage", heal=1), msg("The arch is warm.")])
            for x in [8, 15, 22]:
                square(
                    x,
                    12,
                    [
                        menu(
                            "statue",
                            [
                                ("Leave", []),
                                (
                                    "Break",
                                    [action("infamy", amount=1), flag(f"statue_{x}")],
                                ),
                            ],
                        )
                    ],
                    once=f"statue_{x}",
                )
            square(
                15,
                3,
                [
                    menu(
                        "priestess",
                        [
                            ("Leave", []),
                            ("Attack", [combat([72])]),
                            ("Talk", [msg("DLG-061"), flag("met_priestess")]),
                        ],
                    )
                ],
            )
            stash(15, 5, ["sun_gem"])
        else:
            square(15, 22, [action("menu", id="drowned_gate", special="drowned_gate")])
            for x in [10, 15, 20]:
                square(x, 12, [action("menu", id=f"urn_{x}", special="urn")])
            square(
                15,
                3,
                [
                    menu(
                        "black_statue",
                        [
                            (
                                "Take",
                                [
                                    combat(
                                        [54, 55, 55],
                                        on_win=[
                                            give("crystal_resonator"),
                                            msg("DLG-067"),
                                        ],
                                    )
                                ],
                            ),
                            ("Leave", []),
                        ],
                    )
                ],
                not_item="crystal_resonator",
            )
            square(15, 9, [action("menu", id="circle", special="circle")])
            square(15, 8, [msg("Voss is not here.")])
    elif n == 8:
        rooms = [
            (13, 2, 17, 5),
            (4, 4, 8, 8),
            (22, 4, 26, 8),
            (4, 12, 8, 16),
            (22, 12, 26, 16),
            (10, 12, 20, 16),
        ]
        for x, y, f in [
            (15, 18, [22, 22, 48, 48]),
            (15, 14, [48, 48, 48]),
            (15, 10, [22, 22, 22, 52]),
            (15, 7, [52, 52]),
        ]:
            set_at(x, y, f)
        for y in [20, 16]:
            square(15, y, [msg("Battle-noise rolls through the camp.")])
        square(15, 3, [action("menu", id="wood", special="wood")])
        square(24, 20, [action("menu", id="quartermaster", special="vendor")])
        set_at(12, 14, [20], refill=True)
        set_at(18, 14, [49], refill=True)
        stash(6, 20, [], "t8")
    elif n == 9:
        rooms = [(26, 10, 29, 14), (1, 11, 4, 13)]
        panels = [[4, 12], [6, 10], [8, 12], [10, 10], [12, 12], [14, 10], [16, 10]]
        for x, y, f in [
            (16, 12, [22] * 4),
            (18, 10, [39, 39]),
            (20, 12, [33]),
            (22, 10, [51]),
            (24, 12, [52, 52]),
        ]:
            set_at(x, y, f)
        square(17, 12, [msg("A lifeless chill.")])
        square(19, 12, [msg("A lifeless chill.")])
        square(21, 10, [msg("A hideous laugh.")])
        square(27, 12, [action("menu", id="voss", special="voss")])
    elif n == 10:
        rooms = [(13, 10, 17, 14)]
        square(15, 12, [action("menu", id="hermit", special="hermit")])
    else:
        rooms = [(12, 2, 18, 8), (5, 10, 25, 14), (12, 16, 18, 23)]
        for x, y, f, t in [
            (15, 6, [10] * 4, "t1"),
            (8, 12, [21] * 3, "t4"),
            (22, 12, [31] * 2, "t7"),
            (15, 17, [61], "t8"),
        ]:
            set_at(x, y, f, on_win=[flag("drake_apex")] if t == "t8" else [])
            stash(x, y + 1, [], t)
        set_at(15, 21, [73])
        stash(15, 22, ["diamond", "elder_lens"])
        square(15, 4, [msg("Sulfur hangs in the hollows.")])
    # Connect all specified rooms and feature squares, preserving authored walls.
    for box in rooms:
        rect(grid, box, "floor")
    points = (
        [entry]
        + [[(box[0] + box[2]) // 2, (box[1] + box[3]) // 2] for box in rooms]
        + [r["at"] for r in scripts]
        + [t["at"] for t in traps]
        + [d["at"] for d in doors]
        + panels
    )
    hub = [15, 12]
    if n in [6, 7]:
        points += [
            [x, y]
            for x, y in [
                (10, 10),
                (20, 10),
                (12, 8),
                (18, 8),
                (15, 6),
                (15, 18),
                (7, 16),
                (23, 16),
                (8, 12),
                (15, 12),
                (22, 12),
                (10, 12),
                (20, 12),
                (15, 3),
                (15, 5),
                (15, 9),
                (15, 8),
            ]
        ]
    for p in points:
        line(grid, p, hub)
    if n in [6, 7]:
        for a, b in zip(
            [[13, 20], [13, 19], [10, 19], [10, 17]],
            [[13, 19], [10, 19], [10, 17], [10, 15]],
        ):
            line(grid, a, b)
    if n == 9:
        # Explicit route travels above the set posts, avoiding all five and random rolls.
        route = [entry] + panels + [[16, 8], [27, 8], [27, 12]]
        for a, b in zip(route, route[1:]):
            line(grid, a, b)
        safe = set()
        for a, b in zip(route, route[1:]):
            x, y = a
            while [x, y] != b:
                safe.add((x, y))
                if x != b[0]:
                    x += 1 if x < b[0] else -1
                elif y != b[1]:
                    y += 1 if y < b[1] else -1
            safe.add(tuple(b))
    else:
        safe = set()
    for d in doors:
        grid[d["at"][1]][d["at"][0]] = "door"
    for x, y in panels:
        grid[y][x] = "panel"
    write(
        f"world/sites/{ident}.json",
        [
            dict(
                id=ident,
                name=names[n - 1],
                width=30,
                height=24,
                grid=grid,
                entry=entry,
                pool=pools[n],
                doors=doors,
                panels=panels,
                traps=traps,
                sets=sets,
                safe_route=[list(p) for p in sorted(safe)],
            )
        ],
    )
    write(f"world/scripts/{ident}.json", scripts, kind="scripts")


if __name__ == "__main__":
    main()
