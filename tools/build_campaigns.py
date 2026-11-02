# Version: 0.2.0 | 2026-11-02
"""Record command-only acceptance journeys. No direct state assignment."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from tests.harness import Journey
from cradle.engine.support import party


class Campaign(Journey):
    def __init__(self, home, seed=7):
        super().__init__(home, seed)
        self.visits = 0

    def heal(self):
        e = self.e
        if e.s["phase"] not in ["site", "trail"] or e.s["script_ctx"]:
            return
        for m in party(e, living=True):
            needs = m["hp_cur"] < m["hp_max"] * 0.7 or any(
                v["sev"] in ["broken", "gone"] for v in m["body"].values()
            )
            if not needs:
                continue
            if m["mp_cur"] < 4 and 58 in m.get("rites", []):
                donor = next(
                    (
                        d
                        for d in party(e, living=True)
                        if any(
                            i["item_id"].startswith("nerve_tonic") for i in d["items"]
                        )
                    ),
                    None,
                )
                if donor:
                    self.do(
                        "trail.use_tonic",
                        member=donor["id"],
                        item=next(
                            i["item_id"]
                            for i in donor["items"]
                            if i["item_id"].startswith("nerve_tonic")
                        ),
                        target_member=m["id"],
                    )
            donor = next(
                (
                    d
                    for d in party(e, living=True)
                    if any(i["item_id"].startswith("radium_tonic") for i in d["items"])
                ),
                None,
            )
            if donor:
                ident = next(
                    i["item_id"]
                    for i in donor["items"]
                    if i["item_id"].startswith("radium_tonic")
                )
                self.do(
                    "trail.use_tonic",
                    member=donor["id"],
                    item=ident,
                    target_member=m["id"],
                )
            if (
                e.s["phase"] == "site"
                and 58 in m.get("rites", [])
                and m["mp_cur"] >= 4
                and m["body"]["arm_r"]["sev"] not in ["broken", "gone"]
            ):
                self.do("trail.perform", member=m["id"], feat=58)

    def settle(self, max_rounds=200, win=False):
        e = self.e
        for _ in range(max_rounds):
            if e.s["phase"] == "encounter":
                if not win:
                    self.do("enc.flee")
                else:
                    self.do("enc.fight")
                continue
            if e.s["phase"] == "combat":
                c = e.s["combat"]
                if c["redo_open"]:
                    self.do("menu.return")
                    continue
                for actor, mid in enumerate(e.s["expedition"]["members"], 1):
                    m = next(m for m in e.s["roster"] if m["id"] == mid)
                    if m["vital"] == "dead" or mid in c["assign"]:
                        continue
                    tactic = (
                        "parry"
                        if m["body"]["arm_r"]["sev"] in ["broken", "gone"]
                        else "attack"
                    )
                    self.do("cmb." + tactic, actor=actor)
                continue
            self.heal()
            return
        raise AssertionError("Combat did not finish")

    def walk(self, destination, avoid=True):
        for _ in range(500):
            if self.e.s["world"]["pos"] == list(destination):
                return self
            self.heal()
            before = self.e.s["world"]["map_id"]
            directions = self.path(destination, avoid)
            if not directions:
                return self
            for direction in directions:
                phase = self.e.s["phase"]
                old = list(self.e.s["world"]["pos"])
                delta = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}[
                    direction
                ]
                expected = [old[0] + delta[0], old[1] + delta[1]]
                self.do(phase + ".move", dir=direction)
                st = self.e.s["world"]["sites"].get(before, {})
                if st.get("door_continue"):
                    self.do("site.listen_continue", proceed=True)
                if self.e.s["phase"] in ["encounter", "combat"]:
                    self.settle(
                        win=bool(
                            self.e.s["combat"].get("set_id")
                            or self.e.s["combat"].get("wrestle")
                        )
                    )
                if self.e.s["world"]["map_id"] != before:
                    return self
                if self.e.s["script_ctx"]:
                    return self
                self.heal()
                if self.e.s["phase"] == "post":
                    return self
                if self.e.s["world"]["pos"] != expected:
                    break
        raise AssertionError("Movement did not finish")

    def goto(self, site, mode="saved"):
        for attempt in range(20):
            if self.e.s["phase"] == "post":
                self.do("post.infirmary")
                self.do("post.leave")
            world = self.e.s["world"]
            doc = self.e.lookup(world["map_id"], world["map_id"])
            if site not in ["site06", "site07", "site09"] and world["map_id"] in [
                "ziggurat_sun",
                "ziggurat_drowned",
            ]:
                self.walk((9, 8))
                world = self.e.s["world"]
                doc = self.e.lookup(world["map_id"], world["map_id"])
            if site in ["site06", "site07"] and world["map_id"] == "province":
                self.goto("site05")
                self.point(4, 13)
                self.choose(39 if site == "site06" else 40)
                self.point(26, 13)
                self.choose(1)
                world = self.e.s["world"]
                doc = self.e.lookup(world["map_id"], world["map_id"])
            feature = next(f for f in doc["features"] if f["id"] == site)
            if world["pos"] == feature["pos"]:
                delta = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
                direction = next(
                    d
                    for d, (dx, dy) in delta.items()
                    if 0 <= world["pos"][0] + dx < doc["width"]
                    and 0 <= world["pos"][1] + dy < doc["height"]
                    and doc["grid"][world["pos"][1] + dy][world["pos"][0] + dx]
                    not in ["water", "wall", "solid", "lava"]
                )
                self.do("trail.move", dir=direction)
                self.settle()
            self.walk(feature["pos"])
            if self.e.s["phase"] == "post":
                continue
            self.do("menu.choose", option_key="Y", mode=mode)
            return
        raise AssertionError(("Repeated travel wipe", site))

    def point(self, x, y, avoid=True):
        site = self.e.s["world"]["map_id"]
        for attempt in range(20):
            self.walk((x, y), avoid)
            if self.e.s["phase"] == "post":
                self.goto(site)
                continue
            assert self.e.s["world"]["pos"] == [x, y], (
                self.e.s["world"]["pos"],
                [x, y],
                self.e.s["script_ctx"],
            )
            return
        raise AssertionError(("Repeated site wipe", site, x, y))

    def choose(self, n):
        return self.do("site.choose", option_index=n)

    def provisions(self):
        e = self.e
        for m in party(e, living=True):
            # Free space by selling superseded kits and low-end fire pieces.
            for inst in list(m["items"]):
                ident = inst["item_id"]
                row = e.items[ident]
                if (
                    not inst["bound"]
                    and row["family"] in ["weapon", "armor", "shield", "fire"]
                    and m["in_use"].get(row["family"]) != ident
                ):
                    self.do("shop.sell", member=m["id"], item=ident)
            for ident in [
                "radium_tonic_8"
                if "radium_tonic_8" in e.s["stock"]
                else "radium_tonic_5",
                "nerve_tonic_3",
            ]:
                if ident not in e.s["stock"]:
                    ident = "nerve_tonic_8"
                if (
                    len(m["items"]) < e.rules["kit_cap"]
                    and e.s["expedition"]["treasury"] >= e.items[ident]["cost"]
                ):
                    self.do("shop.buy", member=m["id"], item_id=ident)

    def gear(self):
        e = self.e
        from cradle.engine.outfitter import usable

        for m in party(e, living=True):
            for family in ["armor", "weapon"]:
                options = [
                    e.items[i]
                    for i in e.s["stock"]
                    if e.items[i]["family"] == family and usable(e, m, i)
                ]
                if not options:
                    continue
                row = max(options, key=lambda r: r["value"])
                if (
                    row["id"] != m["in_use"].get(family)
                    and len(m["items"]) < 9
                    and e.s["expedition"]["treasury"] >= row["cost"]
                ):
                    self.do("shop.buy", member=m["id"], item_id=row["id"])

    def make_hollowed(self):
        self.do("session.new", seed=self.e.seed)
        self.do("chr.add", member=1)
        for _ in range(20):
            if self.e.s["roster"][0]["frozen"]:
                return
            self.do("post.leave")
            self.walk((34, 28))
            if self.e.s["phase"] != "post":
                # Swim until a production drowning or nearby battle causes a wipe.
                for _ in range(100):
                    if self.e.s["phase"] == "post":
                        break
                    pos = self.e.s["world"]["pos"]
                    direction = "N" if pos == [34, 28] else "S"
                    self.do("trail.move", dir=direction)
                    if self.e.s["phase"] in ["encounter", "combat"]:
                        self.do("enc.fight")
                        while self.e.s["phase"] == "combat":
                            self.do("cmb.parry", actor=1)
                            self.do("menu.return")
                            if self.e.s["phase"] == "encounter":
                                self.do("enc.fight")
        raise AssertionError("Expected Tribunal Hollowed outcome")


def record(kind, students=False, seed=7):
    with TemporaryDirectory(prefix="cradle-golden-") as home:
        j = Campaign(home, seed)
        j.make_hollowed()
        e = j.e
        if kind == "tribunal":
            return j
        for mid in range(2, 7):
            j.do("chr.add", member=mid)
        for m in e.s["roster"]:
            j.do("credit.withdraw", member=m["id"], amount=m["credit"])
        j.gear()
        j.provisions()
        j.goto("site01")
        j.point(15, 15)
        j.choose(3)
        for _ in range(210):
            j.choose(3)
        j.choose(4)
        j.point(2, 2)
        j.choose(1)
        j.point(26, 18)
        j.point(25, 12)
        if kind == "site_reset":
            j.do("site.exit", save_state=True)
            j.goto("site01", mode="original")
            j.point(15, 15)
            j.choose(3)
            j.choose(4)
            assert e.s["flags"]["shrine_boon"]
            return j
        j.do("site.exit", save_state=True)
        j.walk((37, 24))
        j.do("post.infirmary")
        j.provisions()
        j.goto("site02")
        j.point(25, 21)
        j.do("site.exit", save_state=True)
        j.goto("site03")
        j.point(15, 6)
        j.do("site.exit", save_state=True)
        j.goto("site04")
        j.point(26, 5)
        j.choose(1)
        j.point(25, 14)
        j.point(6, 14)
        j.choose(1)
        j.do("site.exit", save_state=True)
        j.goto("site05")
        j.point(6, 3)
        j.point(4, 13)
        j.choose(39)
        j.point(26, 13)
        j.choose(1)
        j.goto("site06")
        j.point(15, 3)
        j.choose(3)
        j.point(15, 5)
        j.do("site.exit", save_state=True)
        # Back to Province via the plaza, then obtain the Drowned Key.
        j.walk((9, 8))
        j.goto("site02")
        j.point(3, 21)
        j.do("site.exit", save_state=True)
        j.goto("site01")
        j.point(15, 15)
        j.choose(3)
        for _ in range(215):
            j.choose(3)
        j.choose(4)
        j.do("site.exit", save_state=True)
        j.goto("site08")
        j.point(15, 3)
        j.point(24, 20)
        j.gear()
        j.provisions()
        j.do("site.exit", save_state=True)
        j.goto("site10")
        j.point(15, 12)
        j.choose(1)
        j.choose(1)
        j.choose(1)
        j.do("site.exit", save_state=True)
        j.goto("site02")
        j.point(13, 8)
        j.choose(1)
        j.settle(win=True)
        j.do("site.exit", save_state=True)
        j.goto("site11")
        j.point(15, 17, avoid=False)
        if e.s["phase"] in ["combat", "encounter"]:
            j.settle(win=True)
        j.do("site.exit", save_state=True)
        j.goto("site05")
        j.point(4, 13)
        j.choose(40)
        j.point(26, 13)
        j.choose(1)
        j.goto("site07")
        j.choose(3)
        j.point(10, 12)
        j.choose(3)
        j.point(15, 9)
        j.choose(4)
        j.walk((4, 7))
        for _ in range(6):
            j.do("post.infirmary")
        if students:
            for mid in [3, 4, 6]:
                j.do("chr.drop", member=mid)
            for prof in ["antiquarian_mesmerist", "expedition_doctor", "cat_burglar"]:
                j.do("chr.begin_recruit")
                j.do("chr.pick_strain", strain="club_stock")
                j.do("chr.pick_profession", prof=prof)
                j.do("chr.accept", name=prof)
                j.do("chr.add", member=e.s["roster"][-1]["id"])
        for attempt in range(5):
            j.goto("site09")
            j.point(27, 12)
            j.choose(3)
            j.choose(5)
            j.choose(1 if kind == "good" else 2)
            j.settle(win=True)
            if e.s["flags"].get("ending_" + kind):
                break
            for _ in range(6):
                j.do("post.infirmary")
        assert e.s["flags"].get("ending_" + kind), (kind, e.s["flags"])
        return j


def main():
    root = Path(__file__).resolve().parents[1] / "tests/golden"
    for kind in ["tribunal", "site_reset", "good", "evil"]:
        print("Building", kind, flush=True)
        j = record(kind)
        path = root / f"golden_{kind}.txt"
        path.write_text(
            "# Version: 0.2.0 | 2026-11-02\n# TRACE-11/12; AC-Campaign; seed=7\n"
            + "\n".join(json.dumps(cmd, separators=(",", ":")) for cmd in j.commands)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print("Recorded", kind, len(j.commands), j.e.s["quest_score"], flush=True)


if __name__ == "__main__":
    main()
