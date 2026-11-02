# Version: 0.2.0 | 2026-11-02
"""Data menus and keyboard-only entry forms (FR-UIX-002)."""

import math

# Presentation-only form fields. Values are collected then sent as ordinary
# production command arguments; this module never mutates the game aggregate.
FORMS = {
    "util.backup": [("member", "Member number", int), ("slot", "Save slot", int)],
    "util.restore": [("filename", "Backup filename", str)],
    "chr.accept": [("name", "Name", str)],
    "chr.add": [("member", "Member number", int)],
    "chr.drop": [("member", "Member number", int)],
    "chr.rename": [("member", "Member number", int), ("name", "New name", str)],
    "chr.purge": [
        ("member", "Member number", int),
        ("confirm", "Permanently purge? Y/N", bool),
    ],
    "chr.designate_auto": [("automaton", "Mud, Mist or Air", str)],
    "adv.train": [("member", "Member number", int)],
    "adv.train_skill": [("member", "Member number", int), ("skill", "Skill name", str)],
    "adv.learn_feat": [("member", "Member number", int)],
    "credit.withdraw": [("member", "Member number", int), ("amount", "Dollars", int)],
    "credit.deposit": [("amount", "Dollars", int)],
    "shop.list": [("member", "Shopper number", int)],
    "shop.buy": [("member", "Shopper number", int), ("item_no", "Stock number", int)],
    "shop.sell": [("member", "Shopper number", int), ("item", "Kit number", int)],
    "post.inspect": [("member", "Member number", int)],
    "post.use_feat": [("member", "Column number", int)],
    "post.use_item": [("member", "Member number", int), ("item", "Kit number", int)],
    "post.trade": [
        ("src_member", "From member", int),
        ("dst_member", "To member (7 sells)", int),
        ("item", "Kit number", int),
    ],
    "post.distribute": [
        ("item", "Pool number", int),
        ("member", "Recipient number", int),
    ],
    "trail.perform": [("member", "Column number", int)],
    "trail.use_tonic": [
        ("member", "Carrying member", int),
        ("item", "Kit number", int),
        ("target_member", "Recipient number", int),
    ],
    "site.pick_lock": [("member", "Member number", int)],
    "site.disarm": [("member", "Member number", int)],
    "cmb.feat": [],
    "cmb.fire": [("target_rank", "Target rank", int)],
    "cmb.lunge": [("target_rank", "Target rank", int)],
    "cmb.rank": [("rank", "Front, middle or back", str)],
}


class MenuSession:
    def __init__(self, regs):
        self.descriptors = {
            r["id"]: dict(r) for r in regs["presentation/menus.json"]["rows"]
        }
        self.title = ""
        self.options = []
        self.ctx = {}
        self.page = 0
        self.form = None
        self.buffer = ""
        self.error = ""
        self.phase = "boot"
        self.member_ids = []
        self.stock_rows = {}
        self.post_context = None
        self.open(self.descriptors["boot"], {}, [])

    def open(self, descriptor, ctx=None, data_rows=None):
        if isinstance(descriptor, str):
            descriptor = self.descriptors.get(
                descriptor,
                {
                    "id": descriptor,
                    "title": descriptor.replace("_", " ").title(),
                    "options": [],
                },
            )
        self.title = descriptor.get("title", "")
        self.ident = descriptor.get("id", "")
        self.ctx = ctx or {}
        self.page = 0
        self.form = None
        self.buffer = ""
        self.error = ""
        self.options = list(data_rows or descriptor.get("options", []))
        if self.ident == "profession" and self.ctx.get("strain") in [
            "hyena_man",
            "albino_tunnel_folk",
            "ratling",
            "sauroid",
            "ape_man",
            "basalt_brute",
            "fen_man",
            "glider_folk",
            "wing_folk",
            "long_man",
        ]:
            self.options = [
                r
                for r in self.options
                if r["args"]["prof"] in ["white_hunter", "cat_burglar"]
            ]
        if self.ident == "chapter":
            self.options += [
                dict(
                    key="O",
                    label="Designate automaton",
                    verb="chr.designate_auto",
                    args={},
                )
            ]

    def consume(self, pending, projection):
        if self.post_context != projection["post_context"]:
            self.stock_rows = {}
        self.post_context = projection["post_context"]
        self.phase = projection["phase"]
        self.member_ids = projection["expedition"]["members"]
        for ev in pending:
            if ev["kind"] == "STATE" and "stock" in ev["data"]:
                self.stock_rows.update({row["no"]: row for row in ev["data"]["stock"]})
            if ev["kind"] == "MENU":
                d = ev["data"]
                rows = d["slots"]
                # Outfitter stock rows are display data, not menu options.
                if rows and "verb" not in rows[0]:
                    rows = []
                self.open(d["menu_id"], d["ctx"], rows)
        training = projection.get("pending_training")
        if training:
            self.open(
                {
                    "id": "training",
                    "title": f"Skill lessons: {training['left']} left",
                    "options": [
                        dict(
                            key=str(i + 1),
                            label=name.replace("_", " ").title(),
                            verb="adv.train_skill",
                            args={"member": training["member"], "skill": name},
                        )
                        for i, name in enumerate(
                            [
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
                        )
                    ],
                }
            )

    def _command(self, option):
        args = dict(option.get("args", {}))
        verb = option["verb"]
        self.form = {
            "verb": verb,
            "args": args,
            "actor": None,
            "fields": [f for f in FORMS.get(verb, []) if f[0] not in args],
        }
        if verb == "post.distribute" and "item" not in args:
            self.form["fields"] = []
        if verb.startswith("cmb.") and verb not in ["cmb.redo", "cmb.config"]:
            mid = self.ctx.get(
                "member", self.member_ids[0] if self.member_ids else None
            )
            if mid in self.member_ids:
                self.form["actor"] = self.member_ids.index(mid) + 1
        if verb in ["post.use_feat", "trail.perform", "cmb.feat"]:
            feat = args.get("feat", args.get("feat_id"))
            if feat in [1, 2, 3, 4, 44]:
                self.form["fields"].append(("target_member", "Target column", int))
            elif feat in list(range(5, 13)) + list(range(27, 42)) + [
                42,
                45,
                46,
                47,
                50,
            ]:
                self.form["fields"].append(("target_rank", "Target rank", int))
        self.buffer = ""
        if self.form["fields"]:
            return None
        result = {k: self.form[k] for k in ["verb", "args", "actor"]}
        self.form = None
        return result

    def handle_key(self, tok):
        if tok is None:
            return None
        kind, value = tok["kind"], tok["value"]
        if self.form:
            if kind == "escape":
                self.form = None
                self.buffer = ""
                return None
            if kind == "backspace":
                self.buffer = self.buffer[:-1]
            elif kind in ["key", "text"]:
                self.buffer += str(value)
            elif kind == "enter":
                name, label, typ = self.form["fields"][0]
                try:
                    raw = self.buffer.strip()
                    if typ == bool:
                        if raw.upper() not in ["Y", "N", "YES", "NO"]:
                            raise ValueError()
                        val = raw.upper() in ["Y", "YES"]
                    else:
                        val = typ(raw)
                    if typ == str and name not in ["name", "filename"]:
                        val = val.lower()
                    if name == "skin":
                        val = {"b": "bow", "r": "rifle"}.get(val, val)
                except ValueError:
                    self.error = "Enter a valid value."
                    return None
                if (
                    self.form["verb"] == "post.trade"
                    and name == "dst_member"
                    and val == 7
                ):
                    self.form["args"]["sell"] = True
                elif (
                    name
                    in ["member", "src_member", "dst_member", "target_member", "target"]
                    and not self.form["verb"].startswith(("chr.", "adv.", "util."))
                    and type(val) == int
                    and 1 <= val <= len(self.member_ids)
                ):
                    val = self.member_ids[val - 1]
                self.form["args"][name] = val
                self.form["fields"].pop(0)
                if (
                    name == "item_no"
                    and self.form["verb"] == "shop.buy"
                    and self.stock_rows.get(val, {}).get("family") == "fire"
                ):
                    self.form["fields"].append(("skin", "Bow or rifle? B/R", str))
                self.buffer = ""
                self.error = ""
                if not self.form["fields"]:
                    cmd = {k: self.form[k] for k in ["verb", "args", "actor"]}
                    self.form = None
                    return cmd
            return None
        if kind == "page":
            self.page = (self.page + value) % max(1, math.ceil(len(self.options) / 12))
            return None
        if (
            kind == "direction"
            and self.phase in ["trail", "site"]
            and self.ident in ["trail", "site"]
        ):
            return dict(verb=self.phase + ".move", actor=None, args={"dir": value})
        if (
            kind == "key"
            and value in ["3", "E", "S", "W"]
            and self.phase in ["trail", "site"]
            and self.ident in ["trail", "site"]
        ):
            return dict(
                verb=self.phase + ".move",
                actor=None,
                args={"dir": {"3": "N", "E": "E", "S": "S", "W": "W"}[value]},
            )
        if kind == "escape":
            leave = next(
                (
                    o
                    for o in self.options
                    if o["label"].lower() in ["leave", "refuse", "no", "turn back"]
                ),
                None,
            )
            return self._command(leave) if leave else None
        if kind == "enter":
            option = next((o for o in self.options if o["key"] == "ENTER"), None)
            if option is None and any(o["verb"] == "site.choose" for o in self.options):
                return None
            return (
                self._command(option)
                if option
                else dict(verb="menu.return", actor=None, args={})
            )
        if kind in ["key", "text"]:
            visible = self.options[self.page * 12 : (self.page + 1) * 12]
            # Long numeric menus use local 1..12 paging keys, with 0 for ten,
            # '-' and '=' for the final two slots.
            if len(self.options) > 12:
                keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="]
                option = (
                    visible[keys.index(value)]
                    if value in keys and keys.index(value) < len(visible)
                    else None
                )
            else:
                option = next(
                    (o for o in visible if o["key"].upper() == str(value).upper()), None
                )
            if option:
                return self._command(option)
        return None

    def render_rows(self):
        if self.form:
            return [
                self.form["fields"][0][1],
                "> " + self.buffer,
                "ENTER accepts; ESC cancels",
                self.error,
            ]
        rows = []
        visible = self.options[self.page * 12 : (self.page + 1) * 12]
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="]
        for i, option in enumerate(visible):
            rows.append(
                "["
                + (keys[i] if len(self.options) > 12 else option["key"])
                + "] "
                + option["label"]
            )
        if len(self.options) > 12:
            rows.append(
                f"TAB: page {self.page + 1}/{math.ceil(len(self.options) / 12)}"
            )
        if self.phase in ["trail", "site"] and self.ident in ["trail", "site"]:
            rows.append("Arrows / 3 E S W: move")
        return rows
