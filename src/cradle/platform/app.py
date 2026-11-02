# Version: 0.2.0 | 2026-11-02
"""Normal input/dispatch/project/compose loop and data-driven attract reel."""

from copy import deepcopy
from dataclasses import replace
import time
from cradle.engine.state import project
from cradle.ui.menukit import MenuSession
from cradle.ui.inputmap import translate
from cradle.platform import clock
from cradle.platform.config import save_config


class GameApp:
    def __init__(self, engine, composer, renderer, cfg, paths):
        self.engine = engine
        self.play_seed = engine.seed
        self.composer = composer
        self.renderer = renderer
        self.cfg = cfg
        self.paths = paths
        self.menus = MenuSession(engine.regs)
        self.last_input = time.monotonic()
        self.message_until = 0
        self.queued_commands = []
        self.pending = []
        self.demo = []
        self.demo_active = False
        self.demo_sinks = None

    def dispatch(self, cmd):
        if cmd["verb"] == "session.new" and not self.demo_active:
            cmd = {**cmd, "args": {"seed": self.play_seed, **cmd["args"]}}
        result = self.engine.dispatch(cmd)
        self.pending.extend(result)
        self.message_until = time.monotonic() + self.cfg.time_lag * 0.150 * sum(
            ev["kind"] == "MSG" for ev in result
        )
        self.menus.consume(result, project(self.engine.s))
        config = self.engine.s["config_echo"]
        if (config["time_lag"], config["sound"]) != (self.cfg.time_lag, self.cfg.sound):
            self.cfg = replace(
                self.cfg, time_lag=config["time_lag"], sound=config["sound"]
            )
            save_config(self.cfg)
        if self.demo_active and not self.demo and self.engine.s["phase"] == "boot":
            self.stop_demo()
        return result

    def stop_demo(self):
        if self.demo_sinks is not None:
            self.engine.save_sink, self.engine.read_sink = self.demo_sinks
            self.demo_sinks = None
        self.demo_active = False
        self.demo = []

    def start_demo(self):
        # Playback uses normal engine commands but cannot overwrite player slots.
        self.stop_demo()
        self.demo_sinks = self.engine.save_sink, self.engine.read_sink
        slots = {}

        def save_demo(slot, doc):
            slots[slot] = deepcopy(doc)
            return f"demo-slot-{slot}"

        self.engine.save_sink = save_demo
        self.engine.read_sink = lambda slot: deepcopy(slots[slot])
        self.demo = [
            dict(verb=row["verb"], actor=None, args=dict(row["args"]))
            for row in self.engine.data["demo_script"]
        ]
        self.demo_active = True
        self.demo[0]["args"]["seed"] = self.engine.regs[
            "presentation/demo_script.json"
        ]["seed"]

    def demo_next(self):
        # All adaptive choices use the same legal public commands as a player.
        phase = self.engine.s["phase"]
        if phase == "encounter":
            return dict(verb="enc.fight", actor=None, args={})
        if phase == "combat":
            c = self.engine.s["combat"]
            if c["redo_open"]:
                return dict(verb="menu.return", actor=None, args={})
            ids = self.engine.s["expedition"]["members"]
            mid = next(
                m["id"]
                for m in self.engine.s["roster"]
                if m["id"] in ids
                and m["vital"] != "dead"
                and m["id"] not in c["assign"]
            )
            return dict(verb="cmb.thrust", actor=ids.index(mid) + 1, args={})
        if self.engine.s["script_ctx"]:
            self.demo = []
            return dict(verb="session.quit_to_menu", actor=None, args={})
        return (
            self.demo.pop(0)
            if self.demo
            else dict(verb="session.quit_to_menu", actor=None, args={})
        )

    def run(self, smoke=False, screenshot=None):
        smoke_commands = [
            dict(verb=v, actor=None, args=a)
            for v, a in [
                ("session.new", {}),
                ("chr.add", {"member": 1}),
                ("session.save", {"slot": 1}),
                ("session.quit_to_menu", {}),
                ("session.continue", {"slot": 1}),
            ]
        ]
        try:
            cycles = 0
            while True:
                self.renderer.render(
                    self.composer.compose(
                        project(self.engine.s), self.pending, self.menus
                    )
                )
                self.pending = []
                if smoke:
                    if not smoke_commands:
                        if screenshot:
                            self.renderer.save_frame(screenshot)
                        return 0
                    result = self.dispatch(smoke_commands.pop(0))
                    if any(ev["kind"] == "ERROR" for ev in result):
                        return 1
                    continue
                if self.engine.s["phase"] == "demo" and not self.demo_active:
                    self.start_demo()
                if self.demo_active:
                    demo_key = self.renderer.poll()
                    if demo_key == "QUIT":
                        return 0
                    if demo_key is not None:
                        self.stop_demo()
                        self.dispatch(
                            dict(verb="session.quit_to_menu", actor=None, args={})
                        )
                        self.last_input = time.monotonic()
                        continue
                    result = self.dispatch(self.demo_next())
                    if any(ev["kind"] == "ERROR" for ev in result) or (
                        not self.demo and self.engine.s["phase"] == "boot"
                    ):
                        self.stop_demo()
                        self.dispatch(
                            dict(verb="session.quit_to_menu", actor=None, args={})
                        )
                        self.last_input = time.monotonic()
                    clock.pace(self.cfg, 1)
                    continue
                key = self.renderer.poll()
                if key == "QUIT":
                    return 0
                if key is not None:
                    self.last_input = time.monotonic()
                    cmd = self.menus.handle_key(translate(key))
                    if cmd:
                        self.queued_commands.append(cmd)
                if self.queued_commands and time.monotonic() >= self.message_until:
                    self.dispatch(self.queued_commands.pop(0))
                elif (
                    self.engine.s["phase"] == "boot"
                    and time.monotonic() - self.last_input >= 60
                ):
                    self.dispatch(dict(verb="session.demo", actor=None, args={}))
                else:
                    time.sleep(0.01)
                cycles += 1
        except Exception:
            if self.cfg.debug:
                import traceback

                self.paths.logs.mkdir(parents=True, exist_ok=True)
                with (self.paths.logs / "debug.log").open("a") as log:
                    log.write(traceback.format_exc() + "\n")
            raise
        finally:
            self.stop_demo()
            self.renderer.close()
