<!-- Version: 0.1.0 | 2026-11-02 -->
# The Cradle Plateau: The Wrath of Doctor Voss

A deterministic, keyboard-driven expedition CRPG. The authoritative design,
technical specification, and implementation roadmap are in `docs/`.

This is the first implementation increment, **not yet a playable game**.

## Development

Requires Python **3.12.x**. Runtime dependency: `tcod>=16,<17`; no additional
runtime dependencies are introduced by the game.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
cradle --version
cradle-content-check
```

`cradle-content-check [directory]` validates JSON registry envelopes and lint.
The bundled content directory is currently empty, so checking it correctly exits
nonzero. Phase 2 adds content and anchor checks; passing a synthetic pack today
only verifies the loader, **not** the Phase 2 content gate. `cradle` reports the
pending application loop and exits nonzero; `--version` and `--help` work.

Configuration: `CRADLE_HOME` overrides OS user-data paths, with `./userdata` as
the final fallback. Files live under `saves/`, `backups/`, and `logs/`; config is
`config.json`. `CRADLE_DEBUG=1` overrides the stored debug setting. Sound is a
persisted boolean with no audio output (D-2).

## Work-package status

All three documents were read before implementation. This increment follows
Phase 0 → Phase 1, without entering gameplay ahead of the Phase 2 content gate.

| Package | Status / evidence |
| --- | --- |
| WP-0.1 scaffold | Package directories, Python metadata, entry points, install verified; PyInstaller spec is the explicitly permitted scaffold, pending WP-8.1. |
| WP-0.2 test infrastructure | Temp home and seed fixtures; C-8 list implemented; C-9 lexicon unspecified upstream (see below). |
| WP-1.1 errors/types/config/paths | Implemented; `tests/test_config.py`, DTO/import checks in `tests/test_contracts.py`. |
| WP-1.2 events/frame | Implemented; pure constructors and dispatch-owned tick stamping; frame independence tests in `tests/test_contracts.py`. Engine tick integration awaits WP-3.2. |
| WP-1.3 RNG | Implemented; all four draws logged, JSON restart equivalence, replay hash and rejected-input atomicity in `tests/test_rng.py`. |
| WP-1.4 command registry | Entire §6.1 vocabulary registered and phase-tested; envelope validation; menu/handler integration awaits their owning WPs. |
| WP-1.5 loader | Implemented immutable registries, ordered loading, envelope/id validation, string lint and CLI. Synthetic failure tests in `tests/test_contentload.py`; Phase 2 owns content-specific anchor hooks. |
| WP-1.6 save I/O | Structural file boundary implemented and tested in `tests/test_saveio.py`; semantic validation injection is ready for WP-3.1. Production member round-trip acceptance awaits dispatch-produced members in WP-3.2. |
| Phase 2 onward | Not started. |

Pure primitive tests use synthetic config, content and file envelopes. They never
construct playable GameState or members. Gameplay tests must establish all state
via production `Engine.dispatch` commands (technical specification §12a).
No SDL smoke test, playable campaign, release bundle, or release acceptance is
claimed. The scaffold release spec deliberately refuses to package an unfinished
application.

## Specification issues to resolve before affected packages

The roadmap forbids inventing missing game values. The following are recorded
without changing the authoritative documents or silently selecting new values:

- **WP-0.2 / C-9 lexicon:** the docs require an exact period-rhetoric blocklist
  in the fixture but supply no entries. Only the six explicit C-8 lexemes are
  currently enforced. A reviewed C-9 list is needed for that acceptance gate.
- **WP-2.3 item count:** §5.3 says 32 sellables but enumerates **33**, in addition
  to eight quest/bow identities. This gives 181 total items rather than 180.
- **WP-2.6 geography:** several displayed sector/band labels disagree with their
  coordinates and the explicit sector/band formula. The feature table also calls
  the province site anchors nine while listing only eight province sites (D1–5,
  D8, D10–11); D6/D7/D9 are on other planes.
- **WP-2.7/2.8 site geometry:** the mirror-maze wall rectangle list is referenced
  but absent. Several other site corridor connections are not specified, so
  authored connectivity cannot be transcribed exactly without a design decision.
- **WP-2.10 symbols:** the explicit table assigns sabre-tooth id 393 and shifts
  subsequent ids, contradicting the stated row-order mapping. Some foreground
  tokens are blank; `badlands` is used as a color token but absent in §5.10.1.
- **WP-3.1 save shape:** §6.4 SaveDoc and §8.1 GameState differ in world fields,
  automata, expedition optionality, and duplicate treasury locations. A canonical
  lossless snapshot mapping is needed before full semantic validation.
- **WP-4.3 score:** the §8.6 SCORE_W entries sum to **112**, not the asserted 100.
- **WP-6.1 demo:** the script references Folio II at the outfitter although its
  location is D1, and its encounter/victory assumptions need seeded verification.

Next: resolve the missing C-9 list and data contradictions, then transcribe the
Phase 2 registries and install their exact anchor/referential integrity audits.
