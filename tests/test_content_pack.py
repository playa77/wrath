# Version: 0.2.0 | 2026-11-02
"""Real data audits (BR-1/2/3/30/32/33; FR-MAG-002; AC-Content)."""

import json
from pathlib import Path
import subprocess
import sys
import pytest
from cradle.platform.contentload import load_all, lint_strings, check_main
from cradle.platform.contentaudit import audit
from cradle.engine.errors import ContentError

ROOT = Path(__file__).resolve().parents[1]


def test_full_pack_audit():
    # AC-Content / D01–04: counts, anchors, cross references, and reachability.
    regs = load_all(ROOT / "src/cradle/content")
    audit(regs)
    lint_strings(regs)
    assert check_main([]) == 0


def test_authoritative_attribute_and_hp_rows():
    # BR-1/2/3: representative boundaries including all profession extensions.
    regs = load_all(ROOT / "src/cradle/content")
    professions = {r["id"]: r for r in regs["registries/professions.json"]["rows"]}
    assert professions["white_hunter"]["hp_table"] == (
        10,
        20,
        32,
        44,
        56,
        70,
        82,
        94,
        106,
        120,
        130,
        140,
        150,
        160,
        170,
        180,
        190,
        200,
        210,
        220,
    )
    assert professions["antiquarian_mesmerist"]["mp_table"][14:] == (20,) * 6
    strains = {r["id"]: r for r in regs["registries/strains.json"]["rows"]}
    assert dict(strains["long_man"]["caps"]) == {
        "str": 22,
        "int": 13,
        "dex": 15,
        "con": 20,
        "cha": 12,
    }
    assert strains["wing_folk"]["caps"]["dex"] == 22


def test_generation_is_reproducible():
    # ADR-3: committed JSON is reproducible, independent of RNG or wall time.
    paths = list((ROOT / "src/cradle/content").rglob("*.json"))
    before = {p: p.read_bytes() for p in paths}
    for tool in [
        "build_content.py",
        "build_world.py",
        "build_text.py",
        "build_rules.py",
    ]:
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / tool)], check=True, cwd=ROOT
        )
    assert all(p.read_bytes() == data for p, data in before.items())


def test_text_payload_lengths():
    # R-5: fifteen authored folios, 40–90 words each.
    rows = json.loads(
        (ROOT / "src/cradle/content/text/folios.json").read_text(encoding="utf-8")
    )["rows"]
    for row in rows:
        assert 40 <= len(row["text"].split()) <= 90, (
            row["id"],
            len(row["text"].split()),
        )


def test_anchor_corruption_is_rejected(tmp_path):
    # AC-Content / §11: a count mismatch cannot pass a production pack.
    import shutil

    root = tmp_path / "content"
    shutil.copytree(ROOT / "src/cradle/content", root)
    file = root / "registries/menaces.json"
    doc = json.loads(file.read_text(encoding="utf-8"))
    doc["rows"].pop()
    file.write_text(json.dumps(doc), encoding="utf-8", newline="\n")
    with pytest.raises(ContentError, match="78"):
        load_all(root)


def test_removed_transfer_and_functional_silent_audio_contract():
    # AC-FR / D-1 / D-2: retained content has one canonical greeting; no audio API.
    import ast
    from cradle.engine.commands import VERBS

    assert not any("transfer" in verb for verb in VERBS)
    regs = load_all(ROOT / "src/cradle/content")
    texts = [r["text"] for r in regs["text/dialogue.json"]["rows"]]
    assert texts.count("I choose you because Doctor Voss would never suspect you.") == 1
    assert not any("veteran" in text.lower() for text in texts)
    forbidden = {
        "pygame",
        "sounddevice",
        "pyaudio",
        "winsound",
        "audioop",
        "tcod.audio",
        "tcod.sdl.audio",
    }
    for path in (ROOT / "src/cradle").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            assert not any(
                m == banned or m.startswith(banned + ".")
                for m in modules
                for banned in forbidden
            ), path
        assert not any(
            isinstance(node, ast.Attribute) and node.attr == "open_audio_device"
            for node in ast.walk(tree)
        ), path
