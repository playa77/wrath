# Version: 0.2.0 | 2026-11-02
"""Closed site-action interpreter with suspended, engine-owned menus (§6.5)."""

from .support import require, party, held, emit, thaw
from . import events, quests, outfitter, body


def gates(e, g):
    flags = e.s["flags"]
    if g.get("flag") and not flags.get(g["flag"]):
        return False
    if g.get("not_flag") and flags.get(g["not_flag"]):
        return False
    if g.get("once") and flags.get(g["once"]):
        return False
    if g.get("item") and not held(e, g["item"]):
        return False
    if g.get("not_item") and held(e, g["not_item"]):
        return False
    if (
        g.get("dead_set")
        and g["dead_set"] in e.s["world"]["sites"][e.s["world"]["map_id"]]["dead_sets"]
    ):
        return False
    return True


def run_square(e, site, x, y):
    if site == "site03" and not e.s["flags"].get("kilmor_found"):
        return emit("runtime_cold_and_silent")
    actions = []
    # Evaluate all gates before actions, so same-square after-state flavor is
    # shown on revisit, not while the one-time ceremony is still running.
    matches = [
        row
        for row in e.data[site + "_scripts"]
        if row["at"] == [x, y] and gates(e, row["if"])
    ]
    for row in matches:
        actions += thaw(row["then"])
        if row["if"].get("once"):
            actions.append(dict(verb="set_flag", name=row["if"]["once"], value=True))
    return execute(e, actions)


def prompt(e, ident, options, tail=None, special=None):
    e.s["script_ctx"] = dict(
        kind="script", id=ident, options=options, tail=tail or [], special=special
    )
    slots = [
        dict(
            key=str(i),
            label=option["label"],
            verb="site.choose",
            args={"option_index": i},
        )
        for i, option in enumerate(options, 1)
    ]
    return [events.menu(ident, {}, slots)]


def execute(e, actions):
    result = []
    for index, a in enumerate(actions):
        verb = a["verb"]
        tail = actions[index + 1 :]
        if verb == "msg":
            result += emit(a["text"])
        elif verb == "set_flag":
            e.s["flags"][a["name"]] = a.get("value", True)
            quests.update_score(e)
        elif verb == "menu":
            if a.get("special"):
                return result + special_prompt(e, a["special"], tail)
            return result + prompt(e, a["id"], a["options"], tail)
        elif verb == "combat":
            from .encounters import begin_set

            spec = thaw(a)
            spec["on_win"] = spec.get("on_win", []) + tail
            return result + begin_set(e, spec)
        elif verb == "give_item":
            if a.get("treasure"):
                from .combat import treasure

                result += treasure(e, a["treasure"])
            else:
                result += outfitter.give(e, a["id"])
        elif verb == "take_item":
            remove_item(e, a["id"])
        elif verb == "mp_zero":
            for m in party(e):
                m["mp_cur"] = 0
        elif verb == "damage":
            for m in party(e, living=True):
                if a.get("heal"):
                    body.heal(e, m, a["heal"], 1)
                else:
                    dice = a.get("dice", [0, a.get("amount", 0)])
                    amount = e.rng.dice(*dice) if dice[0] else dice[1]
                    body.apply_damage(e, m, amount, a.get("area"))
            if not party(e, living=True):
                from .tribunal import judge

                return result + judge(e)
        elif verb == "transport":
            previous = e.s["world"]["map_id"]
            target = a["map_id"]
            if target == previous:
                e.s["world"]["pos"] = list(a["pos"])
            elif target.startswith("site"):
                from .sites import enter

                result += enter(e, target, "saved")
                e.s["world"]["pos"] = list(a["pos"])
            else:
                e.s["world"].update(map_id=target, pos=list(a["pos"]))
                e.s["phase"] = "trail"
                e.s["script_ctx"] = None
            result.append(events.map_update([a["pos"]]))
        elif verb == "award_con":
            for m in party(e):
                m["attrs"]["con"] = min(
                    e.lookup("strains", m["strain"])["caps"]["con"],
                    m["attrs"]["con"] + a["amount"],
                )
        elif verb == "award_xp":
            for m in party(e, living=True):
                m["xp"] += a["amount"]
        elif verb == "infamy":
            quests.add_infamy(e, a["amount"])
        elif verb == "ending":
            result += quests.end_game(e, a["kind"])
        elif verb == "journal_hint":
            result += emit(a["text"])
        else:
            raise ValueError("Unknown script action " + verb)
    quests.update_score(e)
    return result


def remove_item(e, ident):
    for pool in [m["items"] for m in party(e)] + [e.s["expedition"]["found_items"]]:
        inst = next((i for i in pool if i["item_id"] == ident), None)
        if inst:
            pool.remove(inst)
            return


def special_prompt(e, special, tail=None):
    options = []
    result = []

    def opt(label, **a):
        options.append(dict(label=label, choice=a))

    if special == "filmon":
        return quests.filmon_consult(e) + execute(e, tail or [])
    if special == "shrine":
        for label in e.lookup("runtime", "runtime_menu_choices_55")["values"]:
            opt(label, action=label.lower())
    elif special == "brood":
        for label in e.lookup("runtime", "runtime_menu_choices_61")["values"]:
            opt(label, action=label.lower())
    elif special == "mesmerist":
        if any(57 in m.get("rites", []) or 57 in m["feats"] for m in party(e)):
            return emit("DLG-047") + execute(e, tail or [])
        result += emit("DLG-046")
        opt(e.text("runtime_talk_pay_the_price"), action="talk")
        opt(e.text("runtime_attack"), action="attack")
        opt(e.text("runtime_leave"), action="leave")
    elif special == "chronos":
        key = (
            "DLG-054"
            if e.s["flags"].get("drowned_seen")
            else "DLG-053"
            if e.s["flags"].get("sun_seen")
            else "DLG-052"
            if e.s["flags"].get("chronos_met")
            else "DLG-051"
        )
        e.s["flags"]["chronos_met"] = True
        return emit(key) + execute(e, tail or [])
    elif special == "drake":
        for label in e.lookup("runtime", "runtime_menu_choices_66")["values"]:
            opt(label, action=label.lower())
    elif special == "console":
        for letter in ["A", "B", "C"]:
            for digit in range(1, 10):
                for sign in ["+", "−"]:
                    opt(f"{letter}{digit}{sign}", coords=[letter, digit, sign])
    elif special == "funicular":
        opt(e.text("runtime_engage"), action="engage")
        opt(e.text("runtime_leave"), action="leave")
    elif special == "drowned_gate":
        for label in e.lookup("runtime", "runtime_menu_choices_69")["values"]:
            opt(label, action=label.lower())
    elif special == "urn":
        for label in e.lookup("runtime", "runtime_menu_choices_70")["values"]:
            opt(label, action=label.lower())
    elif special == "circle":
        for label in e.lookup("runtime", "runtime_menu_choices_71")["values"]:
            opt(label, action=label.lower())
    elif special == "wood":
        if e.s["expedition"]["infamy"] >= 1:
            return emit("absent") + execute(e, tail or [])
        if not e.s["flags"].get("wood_met"):
            e.s["flags"]["wood_met"] = True
            result += (
                outfitter.give(e, "folio_V")
                + outfitter.give(e, "folio_XIV")
                + emit("DLG-070")
            )
        else:
            result += emit("DLG-072")
        if not e.s["flags"].get("rite57_held"):
            result += emit("DLG-071")
        quests.update_score(e)
        return result + execute(e, tail or [])
    elif special == "vendor":
        outfitter.open_stock(e, vendor=True)
        return outfitter.list_page(e) + execute(e, tail or [])
    elif special == "voss":
        for label in e.lookup("runtime", "runtime_menu_choices_73")["values"]:
            opt(label, action=label.lower())
    elif special == "voss_feat":
        for n in [5, 44, 49, 54, 57]:
            opt(e.lookup("feats", n)["name"], feat=n)
    elif special == "climax":
        opt(e.text("runtime_fight_doctor_voss"), ending="good", foes=[76])
        opt(e.text("runtime_fight_lord_wood"), ending="evil", foes=[74])
    elif special == "hermit":
        if e.s["flags"].get("bowls_used", 0) >= e.rules["hermit_bowls"]:
            return emit("DLG-090") + execute(e, tail or [])
        opt(e.text("runtime_sit"), action="sit")
        opt(e.text("runtime_leave"), action="leave")
    elif special == "broth":
        for attr, label in e.lookup("runtime", "runtime_menu_choices_78")["values"]:
            opt(label, attr=attr)
    elif special == "second_bowl":
        opt(e.text("runtime_another_bowl_of_the_same_broth"), action="another")
        opt(e.text("runtime_later"), action="later")
    return result + prompt(e, special, options, tail, special)


def choose(e, option_index, **a):
    ctx = e.s["script_ctx"]
    require(ctx and ctx.get("kind") == "script", "runtime_no_pending_script_menu")
    require(
        type(option_index) == int and 1 <= option_index <= len(ctx["options"]),
        "runtime_invalid_menu_option",
    )
    option = ctx["options"][option_index - 1]
    e.s["script_ctx"] = None
    special = ctx.get("special")
    result = []
    tail = ctx["tail"]
    choice = option.get("choice", {})
    act = choice.get("action")
    if not special:
        # Declining Take/Break does not claim a once-ever reward.
        if not option["then"]:
            tail = [a for a in tail if a["verb"] != "set_flag"]
        return execute(e, option["then"] + tail)
    if special == "shrine":
        if act == "pray":
            if not e.s["flags"].get("shrine_boon"):
                require(party(e), "runtime_muster_an_expedition_first")
                party(e)[0]["rites"].append(58)
                e.s["flags"]["shrine_boon"] = True
                result += emit("DLG-021")
            else:
                from .support import credit_money

                result += credit_money(e, 50 * len(party(e)))
        elif act == "destroy" and not e.s["flags"].get("shrine_destroyed"):
            e.s["flags"]["shrine_destroyed"] = True
            quests.add_infamy(e, 2)
        elif act == "inspect":
            result += emit("runtime_an_elder_shrine_intellect_waits_within_the_stone")
    elif special == "brood":
        if act == "ask":
            result += emit("runtime_silence")
        elif act in ["snatch", "distract"]:
            if (
                held(e, "foul_phial")
                and e.s["world"]["sites"]["site04"]["flags"].get("scent")
                != "sweet_phial"
            ):
                result += outfitter.give(e, "old_master_bow") + emit("DLG-043")
            else:
                result += emit("DLG-044")
    elif special == "mesmerist":
        if act == "talk":
            e.s["expedition"]["treasury"] = 0
            for m in party(e):
                m["xp"] -= int(m["xp"] * e.rules["mesmerist_xp_tithe"])
                leader = m["id"] == e.s["expedition"]["members"][0]
                if 57 not in m.get("rites", []) and (leader or m["slots_left"] > 0):
                    m["rites"].append(57)
                    if not leader:
                        m["slots_left"] -= 1
            e.s["flags"]["rite57_held"] = True
            result += emit("DLG-047")
        elif act == "attack":
            return execute(e, [dict(verb="combat", foes=[19, 19, 34, 34])] + tail)
    elif special == "drake" and act != "leave":
        result += emit(
            e.rng.pick(
                [r["id"] for r in e.data["strings"] if r["id"].startswith("purr")]
            )
        ) + emit("nap")
    elif special == "console":
        e.s["world"]["funicular"] = choice["coords"]
        result += emit(" ".join(map(str, choice["coords"])))
    elif special == "funicular" and act == "engage":
        coords = e.s["world"]["funicular"]
        if coords in [["C", 2, "+"], ["C", 2, "−"]]:
            sun = coords[-1] == "+"
            e.s["flags"]["sun_seen" if sun else "drowned_seen"] = True
            return execute(
                e,
                [
                    dict(
                        verb="transport",
                        map_id="ziggurat_sun" if sun else "ziggurat_drowned",
                        pos=[9, 7],
                    )
                ]
                + tail,
            )
        result += emit("thrumming")
    elif special == "drowned_gate" and act != "leave":
        tier = quests.infamy_tier(e)
        allowed = tier == 3 if act == "knock" else held(e, "drowned_key")
        if allowed:
            e.s["flags"]["drowned_gate_entered"] = True
            e.s["world"]["sites"]["site07"]["gate_open"] = True
        result += emit(
            "DLG-064"
            if tier == 3 and act == "knock"
            else "DLG-065"
            if allowed
            else "DLG-062"
            if tier == 0
            else "DLG-063"
        )
    elif special == "urn":
        if act == "take":
            result += outfitter.give(e, "obsidian_urn")
        if act == "break":
            words = e.text("DLG-066").split()
            filler = e.lookup("strings", "STR-C1")["words"]
            scrambled = []
            for word in words:
                scrambled.extend([e.rng.pick(filler) for _ in range(3)] + [word])
            e.s["flags"]["invitation_known"] = True
            result += emit(" ".join(scrambled)) + emit("DLG-066")
    elif special == "circle":
        if act in ["place", "throw"]:
            result += emit("bound")
        elif act in ["turn thrice and wave", "wave and incant"]:
            e.s["world"]["pos"] = [15, 22]
            result += emit("runtime_a_concussion_hurls_the_column_back_to_the_gate")
        elif act == "break":
            require(held(e, "crystal_resonator"), "runtime_the_resonator_is_required")
            remove_item(e, "crystal_resonator")
            e.s["flags"]["deeps_open"] = True
            return execute(
                e, [dict(verb="transport", map_id="deeps", pos=[15, 7])] + tail
            )
    elif special == "voss":
        if act == "fight":
            return execute(
                e,
                [
                    dict(
                        verb="combat",
                        foes=[75],
                        on_win=[dict(verb="ending", kind="good")],
                    )
                ]
                + tail,
            )
        if act == "talk":
            tier = quests.infamy_tier(e)
            result += emit(
                "DLG-080" if tier == 0 else "DLG-081" if tier == 1 else "DLG-082"
            )
            if tier == 0:
                return result + execute(
                    e,
                    [
                        dict(
                            verb="combat",
                            foes=[75],
                            on_win=[dict(verb="ending", kind="good")],
                        )
                    ]
                    + tail,
                )
        if act == "perform a feat":
            return special_prompt(e, "voss_feat", tail)
    elif special == "voss_feat":
        feat = choice["feat"]
        if feat == 57:
            if not any(57 in m.get("rites", []) or 57 in m["feats"] for m in party(e)):
                result += emit("DLG-083")
            else:
                from .feats import can_perform

                caster = next(
                    (
                        m
                        for m in party(e, living=True)
                        if 57 in m.get("rites", []) or 57 in m["feats"]
                    ),
                    None,
                )
                require(caster is not None, e.text("DLG-083"))
                f = can_perform(e, caster, 57, phase="combat")
                caster["mp_cur"] -= f["mp"]
                caster["spent_mp"] = True
                return climax(e, tail)
        else:
            result += emit("DLG-084")
    elif special == "climax":
        return execute(
            e,
            [
                dict(
                    verb="combat",
                    foes=choice["foes"],
                    on_win=[dict(verb="ending", kind=choice["ending"])],
                )
            ]
            + tail,
        )
    elif special == "hermit" and act == "sit":
        return special_prompt(e, "broth", tail)
    elif special == "broth":
        e.s["broth_attr"] = choice["attr"]
        result += broth(e, choice["attr"])
        return (
            result + special_prompt(e, "second_bowl", tail)
            if e.s["flags"]["bowls_used"] < e.rules["hermit_bowls"]
            else result + reveal_hermit(e) + execute(e, tail)
        )
    elif special == "second_bowl":
        if act == "another":
            result += broth(e, e.s["broth_attr"])
        result += reveal_hermit(e)
    quests.update_score(e)
    if special == "shrine" and act in ["pray", "inspect"]:
        return result + special_prompt(e, "shrine", tail)
    return result + execute(e, tail)


def broth(e, attr):
    require(
        e.s["flags"].get("bowls_used", 0) < e.rules["hermit_bowls"],
        "runtime_no_broth_remains",
    )
    for m in party(e):
        m["attrs"][attr] = min(
            e.lookup("strains", m["strain"])["caps"][attr], m["attrs"][attr] + 1
        )
    e.s["flags"]["bowls_used"] = e.s["flags"].get("bowls_used", 0) + 1
    e.s["flags"]["hermit_done"] = True
    return [events.state({"broth": attr})]


def reveal_hermit(e):
    if e.s["flags"].get("hermit_revealed"):
        return []
    e.s["flags"]["hermit_revealed"] = True
    return emit("DLG-090")


def climax(e, tail=None):
    require(
        e.s["world"]["map_id"] == "site09",
        "runtime_no_noticeable_effect_at_this_distance",
    )
    if e.s["combat"] is not None:
        e.s["combat"] = None
        e.s["phase"] = "site"
    e.s["flags"]["climax"] = True
    return emit("DLG-085") + special_prompt(e, "climax", tail)
