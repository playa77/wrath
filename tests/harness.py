# Version: 0.2.0 | 2026-11-02
"""Command-only game setup and recorded production journeys (Doc 2 §12a)."""

from collections import deque
from cradle.main import build_engine


class Journey:
    def __init__(self, home, seed=7):
        self.e, _, _ = build_engine(seed, home)
        self.commands = []

    def do(self, verb, actor=None, allow_error=False, **args):
        cmd = dict(verb=verb, actor=actor, args=args)
        result = self.e.dispatch(cmd)
        if not allow_error:
            errors = [r for r in result if r["kind"] == "ERROR"]
            assert not errors, (cmd, errors)
            self.commands.append(cmd)
        return result

    def muster(self):
        self.do("session.new")
        for mid in range(1, 7):
            self.do("chr.add", member=mid)
        return self

    def settle(self, max_rounds=100):
        for _ in range(max_rounds):
            if self.e.s["phase"] == "encounter":
                self.do("enc.flee")
                continue
            if self.e.s["phase"] == "combat":
                c = self.e.s["combat"]
                if c["redo_open"]:
                    self.do("menu.return")
                    continue
                for index, mid in enumerate(self.e.s["expedition"]["members"], 1):
                    m = next(m for m in self.e.s["roster"] if m["id"] == mid)
                    if m["vital"] != "dead" and mid not in c["assign"]:
                        self.do("cmb.parry", actor=index)
                continue
            return
        raise AssertionError("Encounter did not settle")

    def path(self, destination, avoid=True):
        s = self.e.s
        doc = self.e.lookup(s["world"]["map_id"], s["world"]["map_id"])
        start = tuple(s["world"]["pos"])
        goal = tuple(destination)
        blocked = (
            {
                (x, y)
                for y, row in enumerate(doc["grid"])
                for x, t in enumerate(row)
                if t == "lava" and (x, y) != goal
            }
            if avoid
            else set()
        )
        if avoid:
            blocked |= {tuple(f["at"]) for f in doc.get("sets", [])} | {
                tuple(f["at"]) for f in doc.get("traps", [])
            }
            if s["phase"] == "trail":
                blocked |= {
                    tuple(f["pos"]) for f in doc["features"] if tuple(f["pos"]) != goal
                }
            # Do not accidentally open unrelated scripted menus along a route.
            if s["phase"] == "site":
                blocked |= {
                    tuple(r["at"])
                    for r in self.e.data[doc["id"] + "_scripts"]
                    if any(a["verb"] in ["menu", "damage"] for a in r["then"])
                    and tuple(r["at"]) != goal
                }
        prev = {start: None}
        queue = deque([start])
        found = False
        for_pop = [("N", 0, -1), ("S", 0, 1), ("E", 1, 0), ("W", -1, 0)]
        while queue:
            p = queue.popleft()
            if p == goal:
                found = True
                break
            for d, dx, dy in for_pop:
                q = p[0] + dx, p[1] + dy
                if (
                    0 <= q[0] < doc["width"]
                    and 0 <= q[1] < doc["height"]
                    and q not in prev
                    and q not in blocked
                    and doc["grid"][q[1]][q[0]] not in ["wall", "solid", "water"]
                ):
                    if doc["id"] == "province" and (q[0] in [0, 74] or q[1] in [0, 49]):
                        continue
                    prev[q] = (p, d)
                    queue.append(q)
        if not found and avoid:
            return self.path(destination, False)
        assert found, (doc["id"], start, goal)
        result = []
        p = goal
        while prev[p] is not None:
            p, d = prev[p]
            result.append(d)
        return list(reversed(result))

    def walk(self, destination, avoid=True):
        phase = self.e.s["phase"]
        original = self.e.s["world"]["map_id"]
        for direction in self.path(destination, avoid):
            self.do(phase + ".move", dir=direction)
            if self.e.s["world"]["map_id"] != original:
                return
            if self.e.s["phase"] in ["encounter", "combat"]:
                self.settle()
            if self.e.s["phase"] == "post":
                return
            site = self.e.s["world"]["sites"].get(original, {})
            if site.get("door_continue"):
                self.do("site.listen_continue", proceed=True)
        return self


def run_script(verbs, seed=7, home=None):
    if home is None:
        raise ValueError("Tests must supply an isolated home")
    j = Journey(home, seed)
    for row in verbs:
        if isinstance(row, str):
            j.do(row)
        else:
            j.do(row["verb"], actor=row.get("actor"), **row.get("args", {}))
    return j.e
