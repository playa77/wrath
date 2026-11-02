# Version: 0.2.0 | 2026-11-02
"""Authored text and numeric effect parameters: Doc 1/2 authoritative beats."""

import re
from build_content import write, TECH, section, table


def main():
    dialogue = {}
    source = section(TECH, "#### 5.9.2", "#### 5.9.3")
    for line in source.splitlines():
        match = re.match(r"- \*\*DLG-(\d{3})\*\*", line)
        if match:
            quoted = re.search(r'"([^"]+)"', line)
            if quoted:
                dialogue["DLG-" + match[1]] = quoted[1]
    dialogue.update(
        {
            "DLG-021": "The shrine-intellect grants the Sun-Mind's Boon. Use it in the enclosed places of the Plateau.",
            "DLG-031": "A black-robed phantasm appears above the casket: Doctor Voss, projected by mesmerism.",
            "DLG-032": "Thermal rays from emplaced devices sweep the guest rows. Chairs blacken; the guests fall.",
            "DLG-033": "I am Doctor Voss. What I have done today is small work. Only those who take my cause will thrive in the world I am making. I will burn out every last spark of decency on this plateau — but those who join me will be rewarded.",
            "DLG-034": "A hideous laugh rolls through the vaults.",
            "DLG-035": "The broadcast fades. Charred bodies and empty chairs surround the casket.",
            "DLG-040": "Welcome below, friends of the crag-folk and mesa-folk.",
            "DLG-041": "Only crag-folk and mesa-folk are welcome below.",
            "DLG-043": "You have proven your patience. Take the Old Master-Bow.",
            "DLG-045": "The sweet scent draws the viper closer. It is an attractant.",
            "DLG-048": "Beware the Great Beast. The foul bottle keeps the viper away; sweetness draws her close.",
            "DLG-050": "Monday — Time-Space Reclamation. Tuesday — Matter-Energy Transference. Wednesday — the Sun-Ziggurat.",
            "DLG-051": "Old Chronos studies the party, murmurs about his moving station, and falls asleep.",
            "DLG-052": "Set C2+ for the Sun-Ziggurat. Take the glowing key from the cracked ceiling-lens chamber.",
            "DLG-053": "The Drowned Ziggurat mirrors its twin. Set C2− and remember your steps.",
            "DLG-054": "I cannot do anything else for you",
            "DLG-060": "The crystalline sun-gate will open only to the Sun-Key.",
            "DLG-062": "You haven't done enough infamy to enter here.",
            "DLG-063": "Your conduct is doubtful. You have not yet earned entry.",
            "DLG-064": "Enter, infamous ones.",
            "DLG-065": "The Drowned Key turns. Voss is not in.",
            "DLG-067": "The Resonator binds itself to your hand; you cannot get rid of it.",
            "DLG-071": "Go to the Hidden Enclave. The Old Mesmerist holds the fifty-seventh rite.",
            "DLG-072": "I will repeat the plan. Find Voss in the Ember Deeps; perform the Calling before him, and I will come.",
            "DLG-083": "You do not hold that rite, fool.",
            "DLG-084": "There is no noticeable effect at this distance.",
            "DLG-085": 'A black ether-gate opens. Lord Wood steps through. "Strike now! Strike at Doctor Voss!" Voss cries: "No — destroy Lord Wood, and I will raise you beside me." A blue arc joins the two men. Smoke rises; their coats char as the duel of wills holds them motionless.',
        }
    )
    briefs = [
        "Rescue Kilmor. Search the Halls of the Colossi and bring back his journal.",
        "Attend Kilmor's funeral in the Crag-Folk Burial Vaults.",
        "Find the Sun Priestess in the Sun-Ziggurat. Old Chronos knows the way.",
        "Find the Drowned citadel. Its gate answers to the Drowned Key or great infamy.",
        "Meet Lord Wood at his War-Camp. His plan is our best hope.",
        "Stand before Voss in the Basalt Fastness and perform the Calling. Lord Wood will come.",
    ]
    dialogue.update({f"DLG-{10 + i:03}": s for i, s in enumerate(briefs)})
    write(
        "text/dialogue.json",
        [
            dict(
                id=k,
                text=v,
                preserved=k
                in {
                    "DLG-001",
                    "DLG-002",
                    "DLG-020",
                    "DLG-044",
                    "DLG-061",
                    "DLG-066",
                    "DLG-070",
                    "DLG-080",
                    "DLG-081",
                    "DLG-082",
                    "DLG-085",
                    "DLG-086",
                    "DLG-087",
                    "DLG-090",
                },
            )
            for k, v in sorted(dialogue.items())
        ],
    )
    beats = section(TECH, "Full payload texts", "#### 5.9.2")
    texts = {m[1]: m[2] for m in re.finditer(r"- \*\*([IVX]+)\*\* (.*)", beats)}
    # The topic-map prevails over the V/VI shorthand beat-number typo (Doc 1 R-5).
    texts["V"] = (
        "News from the Long War: Lord Wood holds a northern camp against Voss. His officers gather among supply tents and field surgeries. Folios and dispatches describe the struggle; the expedition must seek his audience while its reputation remains clean. A duel of wills may hold Voss long enough for others to strike."
    )
    texts["VI"] = (
        "The elder sun-cult's armorer-saint taught the mesa bowyers. Elder masters endow their works with true virtues, and give those works to the proven. Patience matters more than violence in the bowyer's challenge: carry an egg away without striking the viper or being struck. Learn which scent repels and which attracts."
    )
    texts["VII"] = (
        "The five tiers are Province, Sun-Ziggurat, Drowned Ziggurat, Ember Deeps, and Séance Tribunal. Elder transit is the only door between them. The twin cities once shared mirrored splendor; exile divided their people. Their halls still reflect one another. A traveler who remembers the steps of one city may understand the other."
    )
    payload = []
    titles = {
        r[0]: r[1]
        for r in table(
            section(TECH, "| # | Title | Payload topic", "Full payload texts")
        )
        if r[0] != "#"
    }
    for key, beat in texts.items():
        if key == "XVI":
            continue
        if key not in ["V", "VI", "VII"]:
            # Authored paragraphs retain every normative beat, without outside lore.
            beat = beat.replace("V as above + ", "").replace('"', "").rstrip(".") + "."
            beat = beat[0].upper() + beat[1:]
            beat += " The account is kept for travelers of the Cradle Plateau. Read it before leaving the post, and weigh its warnings against the reports brought home by other expeditions. What is learned here may guide the next journey; it promises no safety beyond these walls."
        payload.append(dict(id=key, title=titles[key], text=beat))
    write("text/folios.json", payload)
    strings = {
        "menace": "MENACE APPROACHES",
        "afford": "You can't afford that",
        "no_feats": "can learn no new feats at this time",
        "bound": "It will not leave your hand.",
        "absent": "There is no one here.",
        "unpickable": "The lock will not yield to any pick.",
        "unusable": "Unusable",
        "empty": "Nothing happens.",
        "bad_args": "Invalid command arguments.",
        "dead": "This member cannot act.",
        "full": "Kit full.",
        "overflow": "The treasury limit would be exceeded.",
        "no_party": "Muster an expedition first.",
        "saved": "Game saved.",
        "welcome": "The Cradle Plateau: The Wrath of Doctor Voss",
        "blocked": "The way is blocked.",
        "found": "You have found a drake's trove.",
        "thrumming": "A far-off thrumming… nothing more.",
        "sun_opposed": "The Sun-Mind is opposed by the Drowned Mind",
        "courage": "Have courage, mighty travelers",
        "sealed": "The ink has long since run to ruin.",
        "nap": "Remember — Chronos takes long naps.",
        "xp_needed": "XP still needed",
        "not_resident": "That member is not resident at this post.",
        "cannot_fire": "An injured limb prevents firing.",
        "parry_only": "The right arm permits only Parry.",
        "cannot_learn": "This member cannot improve.",
        "stock": "Outfitter stock",
        "treasury_lost": "Carried dollars are lost.",
        "returned": "Returned",
        "hollowed": "Hollowed",
        "tax": "Rest-house stay: $250 plus $25 tax.",
        "forfeit": "Overflow dollars are forfeited.",
    }
    purrs = [
        "The drake purrs like a small boiler.",
        "The drake rolls over and rumbles.",
        "The drake nudges your hand.",
        "The drake shuts one golden eye.",
        "The drake stretches and purrs.",
        "The drake sniffs for a biscuit.",
    ]
    write(
        "text/strings.json",
        [dict(id=k, text=v) for k, v in strings.items()]
        + [dict(id="purr" + str(i), text=v) for i, v in enumerate(purrs)]
        + [
            dict(
                id="STR-C1",
                words="SHADOW BRASS EMBER SALT GLASS WORM LAMP TIDE CROWN DUST WIRE MOTH VEIL ROOT IRON BELL FOAM GLOAM SPAR QUILL ASH REED VAULT HUM".split(),
            )
        ],
    )
    menus = []

    def add(ident, title, opts):
        menus.append(
            dict(
                id=ident,
                title=title,
                region="bottom_center",
                options=[dict(key=k, label=l, verb=v, args=a) for k, l, v, a in opts],
            )
        )

    def sub(key, label, target):
        return (key, label, "menu.choose", {"menu_id": target})

    add(
        "boot",
        "The Cradle Plateau",
        [
            ("1", "Start at Terminus", "session.new", {}),
            sub("2", "Continue", "save_slots"),
            ("3", "Demonstration", "session.demo", {}),
            sub("4", "Utilities", "utilities"),
        ],
    )
    add(
        "utilities",
        "Utilities",
        [
            ("1", "Backup member", "util.backup", {}),
            ("2", "Restore member", "util.restore", {}),
            sub("3", "New game (ERASES)", "erase_confirm"),
            sub("Q", "Leave", "boot"),
        ],
    )
    add(
        "erase_confirm",
        "Erase active saves?",
        [
            ("Y", "Yes", "util.new_game_erase", {"confirm": True}),
            sub("N", "No", "boot"),
        ],
    )
    add(
        "post",
        "Post services",
        [
            sub("1", "Explorers' Club chapter", "chapter"),
            sub("2", "Letter-of-credit", "credit"),
            sub("3", "Outfitter", "outfitter"),
            ("4", "Debrief officer", "post.debrief", {}),
            ("5", "Infirmary", "post.infirmary", {}),
            ("6", "Perform a feat", "post.use_feat", {}),
            ("7", "Use an item", "post.use_item", {}),
            ("8", "Distribute & sell", "post.distribute", {}),
            ("9", "Trade", "post.trade", {}),
            ("I", "Inspect member", "post.inspect", {}),
            sub("S", "Save game", "save_slots"),
            ("L", "Leave Post", "post.leave", {}),
        ],
    )
    add(
        "chapter",
        "Explorers' Club",
        [
            (k, l, v, {})
            for k, l, v in [
                ("N", "New member", "chr.begin_recruit"),
                ("L", "List", "chr.list"),
                ("A", "Add", "chr.add"),
                ("D", "Drop", "chr.drop"),
                ("R", "Rename", "chr.rename"),
                ("P", "Purge", "chr.purge"),
                ("T", "Training", "adv.train"),
                ("F", "Learn feats", "adv.learn_feat"),
            ]
        ]
        + [sub("Q", "Leave", "post")],
    )
    add(
        "credit",
        "Letter-of-credit",
        [
            ("W", "Withdraw", "credit.withdraw", {}),
            ("D", "Deposit", "credit.deposit", {}),
            sub("Q", "Leave", "post"),
        ],
    )
    add(
        "outfitter",
        "Outfitter",
        [
            ("L", "List", "shop.list", {"page": 0}),
            ("C", "Continue", "shop.list", {"next": True}),
            ("B", "Buy", "shop.buy", {}),
            ("T", "Sell", "shop.sell", {}),
            sub("Q", "Leave", "post"),
        ],
    )
    for ident, verb, names in [
        (
            "strain",
            "chr.pick_strain",
            [
                "club_stock",
                "crag_folk",
                "lake_folk",
                "mesa_folk",
                "scrub_folk",
                "STRANGE",
            ],
        ),
        (
            "profession",
            "chr.pick_profession",
            [
                "white_hunter",
                "pugilist",
                "expedition_doctor",
                "scout",
                "cat_burglar",
                "antiquarian_mesmerist",
            ],
        ),
    ]:
        add(
            ident,
            ident.title(),
            [
                (
                    str(i + 1),
                    name.replace("_", " ").title(),
                    verb,
                    {"strain" if ident == "strain" else "prof": name},
                )
                for i, name in enumerate(names)
            ],
        )
    add(
        "accept",
        "Keep this recruit?",
        [("A", "Accept", "chr.accept", {}), ("R", "Reject", "chr.reject", {})],
    )
    add(
        "trail",
        "Trail",
        [
            ("P", "Perform", "trail.perform", {}),
            ("I", "Inspect", "trail.inspect", {}),
            ("U", "Use tonic", "trail.use_tonic", {}),
            ("R", "Rest/camp", "trail.camp_rest", {}),
            sub("G", "Time-lag & sound", "config"),
        ],
    )
    add(
        "site",
        "Site",
        [
            ("L", "Look", "site.look", {}),
            ("P", "Pick lock", "site.pick_lock", {}),
            ("T", "Spot trap", "site.spot_trap", {}),
            ("D", "Disarm", "site.disarm", {}),
            ("U", "Use tonic", "trail.use_tonic", {}),
            ("F", "Perform feat", "trail.perform", {}),
            ("X", "Leave", "menu.choose", {"site_exit_prompt": True}),
        ],
    )
    add(
        "encounter",
        "MENACE APPROACHES",
        [
            (str(i + 1), label, "enc." + verb, {})
            for i, (label, verb) in enumerate(
                [
                    ("Fight", "fight"),
                    ("Accept Menace's Surrender", "accept_surrender"),
                    ("Parley", "parley"),
                    ("Beg for Mercy", "beg_mercy"),
                    ("Flee", "flee"),
                ]
            )
        ],
    )
    add(
        "tactic",
        "Tactic",
        [
            (str(i + 1), v.title(), "cmb." + v, {})
            for i, v in enumerate(
                ["thrust", "attack", "slash", "lunge", "aim", "feat", "parry", "fire"]
            )
        ]
        + [sub("9", "Other", "tactic_other")],
    )
    add(
        "tactic_other",
        "Other",
        [
            ("R", "Rank", "cmb.rank", {}),
            sub("T", "Time lag", "config"),
            sub("S", "Sound", "config"),
            ("D", "Redo", "cmb.redo", {}),
        ],
    )
    add(
        "config",
        "Configuration",
        [
            ("T", "Time lag", "menu.choose", {"configure": "time_lag"}),
            ("S", "Sound", "menu.choose", {"configure": "sound"}),
            ("Q", "Leave", "menu.return", {}),
        ],
    )
    add(
        "save_slots",
        "Save slots",
        [
            (
                str(i),
                ("Autosave" if i == 0 else f"Slot {i}"),
                "menu.choose",
                {"slot": i},
            )
            for i in range(5)
        ],
    )
    write(
        "presentation/menus.json",
        menus,
        regions={
            "member_panel": [0, 0, 120, 12],
            "messages": [0, 12, 60, 12],
            "menace_ranks": [60, 12, 60, 12],
            "area_map": [0, 24, 56, 16],
            "menu": [56, 24, 32, 16],
            "figures": [88, 24, 32, 16],
        },
    )
    write(
        "presentation/demo_script.json",
        [
            dict(id=str(i), verb=v, args=a)
            for i, (v, a) in enumerate(
                [
                    ("session.new", {}),
                    ("chr.add", {"member": 1}),
                    ("chr.add", {"member": 2}),
                    ("chr.add", {"member": 3}),
                    ("chr.add", {"member": 4}),
                    ("chr.add", {"member": 5}),
                    ("chr.add", {"member": 6}),
                    ("credit.withdraw", {"member": 1, "amount": 100}),
                    ("shop.buy", {"item_id": "folio_IV", "member": 1}),
                    ("post.use_item", {"member": 1, "item": "folio_IV"}),
                    ("session.save", {"slot": 1}),
                    ("post.leave", {}),
                ]
                + [("trail.move", {"dir": "S"})] * 6
                + [
                    ("session.quit_to_menu", {}),
                    ("session.continue", {"slot": 1}),
                    ("session.quit_to_menu", {}),
                ]
            )
        ],
        seed=7,
    )


if __name__ == "__main__":
    main()
