# Version: 0.2.0 | 2026-11-02
"""AC-Presentation / FR-UIX-001–003 / C-6 renderer-independent tests."""

from copy import deepcopy
import pytest
from tests.harness import Journey
from cradle.engine.state import project
from cradle.ui.composer import Composer, REGIONS
from cradle.ui.menukit import MenuSession
from cradle.ui.inputmap import translate
from cradle.ui.symbolmap import resolve
from cradle.ui.colors import Colors
from cradle.engine.errors import ContentError


@pytest.mark.parametrize(
    "key,kind,value",
    [
        ("UP", "direction", "N"),
        ("KP_6", "direction", "E"),
        ("DOWN", "direction", "S"),
        ("LEFT", "direction", "W"),
        ("RETURN", "enter", "ENTER"),
        ("ESCAPE", "escape", "ESC"),
        ("BACKSPACE", "backspace", ""),
        ("TAB", "page", 1),
        ("PAGEUP", "page", -1),
        ("S", "key", "S"),
        ("SPACE", "text", " "),
    ],
)
def test_key_translation(key, kind, value):
    # FR-UIX-002: keyboard normalization has no gameplay side effects.
    assert translate(key) == {"kind": kind, "value": value}


def test_every_symbol_and_color_resolves(tmp_path):
    # AC-Presentation: all dictionary entities and all state variants resolve.
    j = Journey(tmp_path)
    colors = Colors(j.e.regs)
    for row in j.e.data["symbols"]:
        for state in [set(), *[{s} for s in row["states"]]]:
            glyph, fg, bg = resolve(row["id"], state, j.e.regs)
            assert (
                0 <= glyph <= 255
                and len(colors.rgb(fg)) == 3
                and len(colors.rgb(bg)) == 3
            )
    assert resolve(65, set(), j.e.regs) == (65, "parchment", "ink")
    with pytest.raises(ContentError):
        colors.rgb("absent")
    with pytest.raises(ContentError):
        resolve(999, set(), j.e.regs)


def test_six_region_frame_and_projection(tmp_path):
    # FR-UIX-001 / C-6: snapshot geometry; all 4,800 cells; no state writes.
    j = Journey(tmp_path).muster()
    composer = Composer(j.e.regs)
    menu = MenuSession(j.e.regs)
    pending = j.do("post.inspect", member=1)
    projection = project(j.e.s)
    before = deepcopy(projection)
    menu.consume(pending, projection)
    frame = composer.compose(projection, pending, menu)
    assert (frame["w"], frame["h"]) == (120, 40)
    assert projection == before
    covered = set()
    for x, y, w, h in REGIONS.values():
        cells = {(xx, yy) for xx in range(x, x + w) for yy in range(y, y + h)}
        assert not cells & covered
        covered |= cells
    assert len(covered) == 4800
    assert any(c["layers"] for row in frame["cells"] for c in row)


def test_menu_forms_and_contextual_movement(tmp_path):
    # FR-UIX-002: forms produce commands, never hand-build engine state.
    j = Journey(tmp_path).muster()
    menu = MenuSession(j.e.regs)
    menu.open("chapter")
    menu.phase = "post"
    assert menu.handle_key(translate("R")) is None
    menu.handle_key(translate("1"))
    menu.handle_key(translate("ENTER"))
    for char in "ALICE":
        menu.handle_key(translate(char))
    cmd = menu.handle_key(translate("ENTER"))
    assert cmd == dict(
        verb="chr.rename", actor=None, args={"member": 1, "name": "ALICE"}
    )
    result = j.e.dispatch(cmd)
    assert result[0]["kind"] != "ERROR"
    menu.open("trail")
    menu.phase = "trail"
    assert menu.handle_key(translate("UP"))["args"] == {"dir": "N"}
    assert menu.handle_key(translate("3"))["args"] == {"dir": "N"}
    menu.open("credit")
    assert menu.handle_key(translate("ESCAPE"))["args"] == {"menu_id": "post"}


def test_paged_script_menu_and_invalid_form(tmp_path):
    # FR-UIX-002: all 54 coordinate selections remain reachable via paging.
    j = Journey(tmp_path)
    menu = MenuSession(j.e.regs)
    options = [
        dict(
            key=str(i),
            label=f"Choice {i}",
            verb="site.choose",
            args={"option_index": i},
        )
        for i in range(1, 55)
    ]
    menu.open({"id": "console", "title": "Coordinates", "options": options})
    menu.handle_key(translate("TAB"))
    cmd = menu.handle_key(translate("1"))
    assert cmd["args"]["option_index"] == 13
    menu.open("credit")
    menu.handle_key(translate("D"))
    menu.handle_key(translate("X"))
    assert menu.handle_key(translate("ENTER")) is None
    assert menu.error
    menu.handle_key(translate("ESCAPE"))
    assert menu.form is None


def test_silent_config_is_persistable(tmp_path):
    # D-2 / FR-UIX-003: toggle updates settings and inert flag only.
    j = Journey(tmp_path).muster()
    result = j.do("menu.choose", configure="sound")
    assert j.e.s["config_echo"]["sound"] is False
    assert any(ev["kind"] == "SFX_FLAG" for ev in result)
    before = deepcopy(j.e.s)
    result = j.do("menu.choose", configure="time_lag")
    assert j.e.s["config_echo"]["time_lag"] == 5
    assert j.e.s["roster"] == before["roster"]


def test_fire_skin_form_uses_displayed_stock_metadata(tmp_path):
    # FR-TWN-002 / RS-1: bow/rifle is a skin choice on the same stock identity.
    j = Journey(tmp_path).muster()
    menu = MenuSession(j.e.regs)
    j.do("credit.withdraw", member=1, amount=100)
    page = next(i // 12 for i, ident in enumerate(j.e.s["stock"]) if ident == "fire_1")
    pending = j.do("shop.list", member=1, page=page)
    menu.consume(pending, project(j.e.s))
    number = next(i + 1 for i, ident in enumerate(j.e.s["stock"]) if ident == "fire_1")
    menu.handle_key(translate("B"))
    menu.handle_key(translate("1"))
    menu.handle_key(translate("ENTER"))
    for c in str(number):
        menu.handle_key(translate(c))
    assert menu.handle_key(translate("ENTER")) is None
    menu.handle_key(translate("R"))
    cmd = menu.handle_key(translate("ENTER"))
    assert cmd["args"]["skin"] == "rifle"
    assert j.e.dispatch(cmd)[0]["kind"] != "ERROR"
    assert j.e.s["roster"][0]["items"][-1]["skin"] == "rifle"


def test_pacing_and_unattended_demo(tmp_path, monkeypatch):
    # AC-Presentation / ADR-6 / D-2: lag endpoints differ; demo reaches boot.
    from cradle.platform.clock import pace
    from cradle.platform.config import Config
    from cradle.platform.app import GameApp

    calls = []
    monkeypatch.setattr("cradle.platform.clock.time.sleep", calls.append)
    pace(Config(time_lag=0), 2)
    pace(Config(time_lag=9), 2)
    assert calls == pytest.approx([2.7])
    e, paths, cfg = __import__("cradle.main", fromlist=["build_engine"]).build_engine(
        7, tmp_path
    )
    app = GameApp(e, None, None, cfg, paths)
    app.dispatch(dict(verb="session.new", actor=None, args={}))
    app.dispatch(dict(verb="session.save", actor=None, args={"slot": 1}))
    saved = {p: p.read_bytes() for p in paths.home.rglob("*.json")}
    original_sinks = e.save_sink, e.read_sink
    app.dispatch(dict(verb="session.quit_to_menu", actor=None, args={}))
    app.dispatch(dict(verb="session.demo", actor=None, args={}))
    app.start_demo()
    for _ in range(500):
        result = app.dispatch(app.demo_next())
        assert not any(ev["kind"] == "ERROR" for ev in result)
        if not app.demo and e.s["phase"] == "boot":
            break
    else:
        pytest.fail("Demo failed to return to boot")
    assert (e.save_sink, e.read_sink) == original_sinks
    assert {p: p.read_bytes() for p in paths.home.rglob("*.json")} == saved
    app.start_demo()
    app.dispatch(app.demo_next())
    app.stop_demo()  # interruption restores the player's persistence too
    assert (e.save_sink, e.read_sink) == original_sinks
    assert {p: p.read_bytes() for p in paths.home.rglob("*.json")} == saved


@pytest.mark.parametrize("character", ["0", "1", "3", "9", "a", "-", "="])
def test_real_tcod_key_names(character):
    # C-2 / FR-UIX-002: SDL names digits N0..N9, unlike string test inputs.
    import tcod.event
    from types import SimpleNamespace

    key = SimpleNamespace(sym=tcod.event.KeySym(ord(character)))
    token = translate(key)
    assert token["kind"] == "key" and token["value"] == character.upper()


def test_feat_menus_offer_legal_known_and_learnable_choices(tmp_path):
    # FR-TWN-006 / FR-ADV-003: players select offerings, not undocumented IDs.
    j = Journey(tmp_path).muster()
    e = j.e
    menu = MenuSession(e.regs)
    pending = j.do("post.use_feat", member=2)
    menu.consume(pending, project(e.s))
    assert all(o["args"]["feat"] == 1 for o in menu.options)
    assert menu.handle_key(translate("1")) is None
    menu.handle_key(translate("1"))
    cmd = menu.handle_key(translate("ENTER"))
    assert cmd["args"] == {"member": 2, "feat": 1, "target_member": 1}
    assert e.dispatch(cmd)[0]["kind"] != "ERROR"
    j.do("credit.withdraw", member=2, amount=150)
    pending = j.do("adv.learn_feat", member=2)
    menu.consume(pending, project(e.s))
    assert menu.options[0]["args"]["feat_id"] == 22
    cmd = menu.handle_key(translate("1"))
    assert e.dispatch(cmd)[0]["kind"] != "ERROR"
    assert 22 in e.s["roster"][1]["feats"]


def test_service_columns_map_to_roster_ids_after_recruitment(tmp_path):
    # FR-UIX-002 / FR-CHR-001: column 6 can contain roster member 7.
    j = Journey(tmp_path).muster()
    e = j.e
    j.do("chr.drop", member=6)
    j.do("chr.begin_recruit")
    j.do("chr.pick_strain", strain="club_stock")
    j.do("chr.pick_profession", prof="white_hunter")
    j.do("chr.accept", name="New Hunter")
    j.do("chr.add", member=7)
    menu = MenuSession(e.regs)
    menu.consume([], project(e.s))
    menu.open("post")
    menu.handle_key(translate("I"))
    menu.handle_key(translate("6"))
    cmd = menu.handle_key(translate("ENTER"))
    assert cmd["args"]["member"] == 7
    assert e.dispatch(cmd)[0]["data"]["member"]["name"] == "New Hunter"
    menu.open("post")
    menu.handle_key(translate("9"))
    for value in ["1", "6", "1"]:
        for c in value:
            menu.handle_key(translate(c))
        cmd = menu.handle_key(translate("ENTER"))
    assert cmd["args"]["dst_member"] == 7 and not cmd["args"].get("sell")
    assert e.dispatch(cmd)[0]["kind"] != "ERROR"
    assert len(e.s["roster"][-1]["items"]) == 5
