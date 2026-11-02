# Version: 0.2.0 | 2026-11-02
"""Composition root for both SDL play and deterministic headless replay."""

import argparse
from dataclasses import asdict
from functools import partial
from importlib.metadata import version
from pathlib import Path
import sys

from cradle.platform.config import resolve_paths, load_config, Paths
from cradle.platform.contentload import load_all, lint_strings
from cradle.platform import saveio
from cradle.engine.rng import SeededRng
from cradle.engine.state import new_game
from cradle.engine.core import Engine
from cradle.engine import persistence


def build_engine(seed=0, home=None):
    paths = resolve_paths()
    if home is not None:
        paths = Paths(Path(home), paths.content)
    cfg = load_config(paths.config)
    regs = load_all(paths.content)
    lint_strings(regs)
    rng = SeededRng(seed)
    placeholder = new_game(seed, regs["registries/rules.json"]["rows"][0])
    placeholder["phase"] = "boot"
    engine = Engine(
        placeholder,
        rng,
        regs,
        partial(
            saveio.write_slot,
            paths=paths,
            validator=partial(persistence.validate, regs=regs),
        ),
        partial(
            saveio.read_slot,
            paths=paths,
            validator=partial(persistence.validate, regs=regs),
        ),
        partial(
            saveio.backup_member, paths=paths, validator=persistence.validate_member
        ),
        partial(
            saveio.restore_member, paths=paths, validator=persistence.validate_member
        ),
        partial(saveio.erase_all, paths=paths),
    )
    engine.seed = seed
    engine.s["config_echo"] = {k: v for k, v in asdict(cfg).items() if k != "path"}
    engine.s["config_echo"]["version"] = version("cradle-wrath")
    return engine, paths, cfg


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="The Cradle Plateau: The Wrath of Doctor Voss"
    )
    parser.add_argument("--version", action="version", version=version("cradle-wrath"))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--screenshot", type=Path, help="Save the final smoke frame to a PNG"
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Render a finite boot/new/save/continue smoke sequence",
    )
    args = parser.parse_args(argv)
    try:
        engine, paths, cfg = build_engine(args.seed)
        from cradle.ui.composer import Composer
        from cradle.render.text_renderer import TextRenderer
        from cradle.platform.app import GameApp

        composer = Composer(engine.regs)
        renderer = TextRenderer(cfg, engine.regs)
        return GameApp(engine, composer, renderer, cfg, paths).run(
            smoke=args.smoke, screenshot=args.screenshot
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
