# Version: 0.2.0 | 2026-11-02
"""Transactional command facade. All production mutations pass through dispatch."""

from copy import deepcopy
from importlib import import_module
from . import commands, events, creation, state, persistence, training, outfitter
from .errors import DomainError, SaveError
from .support import require, thaw, party


class Engine:
    def __init__(
        self,
        state,
        rng,
        regs,
        save_sink,
        read_sink=None,
        backup_sink=None,
        restore_sink=None,
        erase_sink=None,
    ):
        self.s = state
        self.rng = rng
        self.regs = regs
        self.save_sink = save_sink
        self.read_sink = read_sink
        self.backup_sink = backup_sink
        self.restore_sink = restore_sink
        self.erase_sink = erase_sink
        self.data = {
            (
                doc["registry"] + "_scripts"
                if path.startswith("world/scripts/")
                else doc["registry"]
            ): thaw(doc["rows"])
            for path, doc in regs.files.items()
        }
        self.rules = self.data["rules"][0]
        self.items = {
            r["id"]: r
            for name in ["items", "tonics", "folio_items", "valuables"]
            for r in self.data[name]
        }
        self.seed = 0
        self.event_log = []

    @property
    def state(self):
        return self.s

    def lookup(self, name, ident):
        row = next((r for r in self.data.get(name, []) if r.get("id") == ident), None)
        require(row is not None, f"Unknown {name} identity: {ident}")
        return row

    def text(self, ident):
        row = next(
            (
                r
                for name in ["strings", "dialogue", "runtime"]
                for r in self.data[name]
                if r["id"] == ident
            ),
            None,
        )
        return row.get("text", ident) if row else ident

    def dispatch(self, cmd):
        before = state.clone(self.s)
        was_script = bool(self.s.get("script_ctx"))
        verb = cmd.get("verb", "") if isinstance(cmd, dict) else ""
        rng_before = self.rng.checkpoint()
        try:
            commands.validate(cmd, self.s["phase"])
            self.rng.tick = self.s["tick"] + 1
            self.rng.caller = cmd["verb"]
            self.current_verb = cmd["verb"]
            args = deepcopy(cmd["args"])
            if cmd.get("actor") is not None:
                ids = self.s["expedition"]["members"]
                require(cmd["actor"] <= len(ids), "runtime_invalid_column_member")
                args.setdefault("member", ids[cmd["actor"] - 1])
            path = commands.VERBS[cmd["verb"]][1]
            module, handler = path.split(".")
            fn = (
                getattr(self, handler)
                if module == "core"
                else getattr(import_module("cradle.engine." + module), handler)
            )
            result = fn(**args) if module == "core" else fn(self, **args)
            if (
                was_script
                and self.s["script_ctx"] is None
                and self.s["phase"] in ["site", "trail"]
                and not any(ev["kind"] == "MENU" for ev in result or [])
            ):
                result = (result or []) + [events.menu(self.s["phase"], {}, [])]
            self.s["tick"] += 1
            if self.s["config_echo"].get("debug"):
                state.check_invariants(self.s)
            result = events.stamp(deepcopy(result or []), self.s["tick"])
            for event in result:
                if event["kind"] == "MENU":
                    self.s["menu_id"] = event["data"]["menu_id"]
            self.event_log.extend(deepcopy(result))
            # Keep interactive diagnostics bounded; simcli retains the returned stream.
            if len(self.event_log) > 512:
                del self.event_log[:-512]
            return result
        except (DomainError, SaveError) as exc:
            self.s = before
            self.rng.rollback(rng_before)
            error = exc if isinstance(exc, DomainError) else DomainError(verb, str(exc))
            error.reason = self.text(error.reason)
            error.verb = verb
            return [events.error(error, tick=self.s["tick"])]
        except (TypeError, KeyError, ValueError, IndexError, AttributeError) as exc:
            self.s = before
            self.rng.rollback(rng_before)
            # Bad envelopes and missing handler args are rule rejections, not crashes.
            return [
                events.error(
                    DomainError(verb, self.text("bad_args") + " " + str(exc)),
                    tick=self.s["tick"],
                )
            ]

    def session_new(self, seed=None, **a):
        if seed is not None:
            require(type(seed) == int, "runtime_seed_must_be_an_integer")
            self.seed = seed
        self.rng.reseed(self.seed)
        self.rng.caller = "session.new"
        self.rng.tick = 1
        config = self.s["config_echo"]
        self.s = state.new_game(self.seed, self.rules)
        self.s["config_echo"] = config
        self.s["phase"] = "post"
        post = self.lookup("posts", self.rules["initial_post"])
        self.s["post_context"] = post["id"]
        self.s["world"].update(
            map_id=post["map_id"], pos=list(post["pos"]), visited_posts=[post["id"]]
        )
        self.s["automata"] = thaw(self.rules["automata"])
        creation.starter_six(self)
        outfitter.open_stock(self)
        return self.autosave() + [events.menu("post", {}, [])]

    def session_continue(self, slot=0, **a):
        require(self.read_sink is not None, "runtime_read_sink_unavailable")
        doc = self.read_sink(slot)
        restored, rng_state = persistence.restore(doc)
        self.rng.restore(rng_state)
        self.s = restored
        return [events.menu("post", {}, []), events.state({"continued": slot})]

    def session_save(self, slot=1, **a):
        require(type(slot) == int and 1 <= slot <= 4, "runtime_manual_slots_are_1_4")
        return [
            events.save_written(
                str(self.save_sink(slot, persistence.snapshot(self.s, self.rng)))
            )
        ]

    def autosave(self):
        require(self.s["phase"] == "post", "runtime_autosaves_require_a_post_snapshot")
        return [
            events.save_written(
                str(self.save_sink(0, persistence.snapshot(self.s, self.rng)))
            )
        ]

    def session_demo(self, **a):
        self.s["phase"] = "demo"
        return [events.state({"demo": True})]

    def quit_to_menu(self, **a):
        self.s["phase"] = "boot"
        self.s["script_ctx"] = None
        return [events.menu("boot", {}, [])]

    def leave_post(self, **a):
        require(party(self), self.text("no_party"))
        require(
            self.s["pending_training"] is None, "runtime_finish_skill_training_first"
        )
        result = self.autosave()
        self.s["phase"] = "trail"
        self.s["menu_id"] = "trail"
        return result + [events.menu("trail", {}, [])]

    def arrive(self, post):
        self.s["post_context"] = post["id"]
        self.s["phase"] = "post"
        self.s["world"].update(map_id=post["map_id"], pos=list(post["pos"]))
        self.s["script_ctx"] = None
        self.s["combat"] = None
        self.s["world"]["plane_return"] = None
        for m in party(self):
            m["resident_post"] = post["id"]
        if post["id"] not in self.s["world"]["visited_posts"]:
            self.s["world"]["visited_posts"].append(post["id"])
        result = training.divide_xp(self)
        outfitter.open_stock(self)
        return result + self.autosave() + [events.menu("post", {}, [])]

    def backup_member(self, member, slot=0, **a):
        require(
            self.backup_sink is not None and self.read_sink is not None,
            "runtime_backup_unavailable",
        )
        doc = self.read_sink(slot)
        persistence.validate(doc)
        m = next((m for m in doc["roster"] if m["id"] == member), None)
        require(m is not None, "runtime_unknown_member")
        return [events.save_written(str(self.backup_sink(m)))]

    def restore_member(self, filename, **a):
        require(self.restore_sink is not None, "runtime_restore_unavailable")
        require(len(self.s["roster"]) < self.rules["roster_cap"], "runtime_roster_full")
        m = self.restore_sink(filename)
        persistence.validate_member(m)
        ids = {m["id"] for m in self.s["roster"]}
        m = deepcopy(m)
        m["id"] = next(
            i for i in range(1, self.rules["roster_cap"] + 1) if i not in ids
        )
        m["resident_post"] = self.s["post_context"]
        self.s["roster"].append(m)
        return [events.state({"restored": m["id"]})]

    def new_game_erase(self, confirm=False, **a):
        if confirm is not True:
            return [events.menu("boot", {}, [])]
        require(self.erase_sink is not None, "runtime_erase_sink_unavailable")
        self.erase_sink(True)
        return self.session_new()

    def configure(self, time_lag=None, sound=None, **a):
        if time_lag is not None:
            require(
                type(time_lag) == int and 0 <= time_lag <= 9, "runtime_invalid_time_lag"
            )
            self.s["config_echo"]["time_lag"] = time_lag
        if sound is not None:
            require(type(sound) == bool, "runtime_invalid_sound_flag")
            self.s["config_echo"]["sound"] = sound
        return [
            events.state({"config": self.s["config_echo"]}),
            events.sfx_flag("config"),
        ]

    def menu_choose(
        self,
        option_key=None,
        menu_id=None,
        slot=None,
        configure=None,
        resthouse=False,
        site_exit_prompt=False,
        **a,
    ):
        if site_exit_prompt:
            require(
                self.s["phase"] == "site", "runtime_leave_site_prompt_requires_a_site"
            )
            return [
                events.menu(
                    "leave_site",
                    {},
                    [
                        dict(
                            key="S",
                            label=self.text("runtime_save_site_state_and_leave"),
                            verb="site.exit",
                            args={"save_state": True},
                        ),
                        dict(
                            key="R",
                            label=self.text("runtime_leave_without_saving"),
                            verb="site.exit",
                            args={"save_state": False},
                        ),
                        dict(
                            key="N",
                            label=self.text("runtime_stay_here"),
                            verb="menu.return",
                            args={},
                        ),
                    ],
                )
            ]
        if resthouse:
            from .infirmary import stay

            self.s["script_ctx"] = None
            return stay(self, resthouse=True)
        if menu_id:
            self.lookup("menus", menu_id)
            return [events.menu(menu_id, {}, [])]
        if slot is not None:
            require(
                self.s["phase"] in ["post", "boot"],
                "runtime_save_load_selection_requires_a_post_or_boot_menu",
            )
            return (
                self.session_save(slot)
                if self.s["phase"] == "post"
                else self.session_continue(slot)
            )
        if configure == "sound":
            return self.configure(sound=not self.s["config_echo"]["sound"])
        if configure == "time_lag":
            return self.configure(time_lag=(self.s["config_echo"]["time_lag"] + 1) % 10)
        if self.s["script_ctx"] and self.s["script_ctx"].get("kind") == "script":
            from .scripts import choose

            return choose(self, int(option_key))
        if self.s["script_ctx"] and self.s["script_ctx"].get("kind") == "site_approach":
            from .sites import enter

            ctx = self.s["script_ctx"]
            self.s["script_ctx"] = None
            return (
                enter(self, ctx["site"], a.get("mode", "saved"))
                if str(option_key).upper() in ["1", "Y"]
                else [events.menu("trail", {}, [])]
            )
        descriptor = self.lookup("menus", self.s["menu_id"])
        option = next(
            (
                x
                for x in descriptor["options"]
                if x["key"].upper() == str(option_key).upper()
            ),
            None,
        )
        require(option is not None, "runtime_unknown_option")
        nested = {"verb": option["verb"], "actor": None, "args": option["args"]}
        commands.validate(nested, self.s["phase"])
        path = commands.VERBS[nested["verb"]][1]
        mod, handler = path.split(".")
        fn = (
            getattr(self, handler)
            if mod == "core"
            else getattr(import_module("cradle.engine." + mod), handler)
        )
        return fn(**nested["args"]) if mod == "core" else fn(self, **nested["args"])

    def menu_return(self, **a):
        if self.s["script_ctx"] and self.s["script_ctx"].get("kind") == "script":
            if self.s["script_ctx"].get("id") == "resthouse":
                self.s["script_ctx"] = None
            else:
                from .scripts import prompt

                ctx = self.s["script_ctx"]
                return prompt(
                    self, ctx["id"], ctx["options"], ctx["tail"], ctx.get("special")
                )
        if self.s["phase"] == "combat" and self.s["combat"]["redo_open"]:
            from .combat import run_round

            return run_round(self)
        return [
            events.menu(
                {
                    "post": "post",
                    "trail": "trail",
                    "site": "site",
                    "combat": "tactic",
                    "encounter": "encounter",
                }.get(self.s["phase"], "boot"),
                {},
                [],
            )
        ]
