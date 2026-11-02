<!-- Version: 0.2.0 | 2026-11-02 -->
# The Cradle Plateau: The Wrath of Doctor Voss

A deterministic, keyboard-driven expedition CRPG for Python 3.12 and tcod.
Explore the Plateau, recruit a six-member expedition, manage credit and equipment,
visit eleven sites, and follow Filmon's investigation to either ending. Play
continues after the ending rewards.

## Install and play

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
cradle --seed 7
```

On Windows, activate `.venv\Scripts\activate` instead. The only direct runtime
dependency is `tcod>=16,<17`; the licensed bitmap font and content are bundled.

Start at Terminus, open the Explorers' Club chapter, and add members 1–6 to your
expedition. The starter roster is supplied; it is not automatically mustered.
Withdraw member credit at the counter before shopping. Equip carried gear through
Use Item. Read folios at posts, and distribute found items before using them.

Arrows or numpad 8/6/2/4 move. The alternate diamond is 3/E/S/W. Menus use the
shown digit or bracket letter. ENTER accepts a form or continues; ESC leaves where
Leave is offered. TAB/PgUp/PgDn page long menus. In combat, assign every living
member, then ENTER executes the round; Redo clears the assignments first.

Manual saves are post-only (slots 1–4); slot 0 is the autosave. Continue resumes at
the recorded post. Utilities export/import members and erase active slots only
with explicit confirmation. Set `CRADLE_HOME` to choose local storage. Configuration
and the functional silent sound toggle persist separately; `CRADLE_DEBUG=1`
enables invariant checks and exception logging.

## Verify

```sh
cradle-content-check
python -m pytest --cov=cradle.engine --cov-report=term-missing --cov-fail-under=90
python -m cradle.simcli tests/golden/golden_good.txt --seed 7 --hash
python -m cradle.simcli tests/golden/golden_evil.txt --seed 7 --hash
cradle --smoke
```

`--smoke` renders boot/new/save/continue and exits. Add `--screenshot frame.png` to
export the final logical frame. On a Linux host without a display, the smoke
command supports `SDL_VIDEODRIVER=dummy SDL_RENDER_DRIVER=software`.

The four primary golden command scripts replay three times each and compare both
RNG and event-stream hashes. A further command-only journey earns XP, pays for
training, and learns every ordinary feat for the effect-router tests. Tests never
inject levels, inventory, or quest flags into playable state.

## Build a desktop bundle

```sh
python -m pip install -e '.[dev,release]'
pyinstaller --noconfirm deploy/pyinstaller.spec
dist/cradle/cradle --smoke
```

The one-folder bundle includes content JSON, CP437 font, license notices, and
package version metadata. Build independently on each target OS. The verification
workflow runs on Linux, Windows and macOS and uploads each bundle.

The source documents and work packages are in `docs/`. Deliberate resolutions of
source contradictions, including the corrected 182-item count, are recorded in
[implementation decisions](docs/implementation_decisions.md). Read the
[verification audit](docs/verification_audit.md) for measured results and the
remaining release sign-off checks. Version 0.2.0 is an implementation candidate;
no unverified v1.0.0 release tag is claimed.
