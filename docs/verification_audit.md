<!-- Version: 0.2.0 | 2026-11-02 -->
# Implementation and verification audit

Prepared by Codex, 2026-11-02. Base: upstream `main` at `872e15c`.
This is an implementation-candidate audit, not a v1.0.0 release certification.
The original design/specification remain authoritative subject to the explicit
[gap decisions](implementation_decisions.md) authorized by the user.

## Implemented work packages

Phases 0–1 are retained from upstream. Phases 2–6 now provide the content pack,
post services, world/site simulation, combat and feats, complete quest scripts,
six-region keyboard UI, SDL renderer, application loop and headless replay CLI.
Phase 7 adds command-only campaigns, branch tests, properties and coverage gates.
Phase 8 supplies the PyInstaller bundle, asset licensing, build instructions and
three-OS packaging workflow. Final release sign-off is tracked separately below.

## Acceptance evidence

| Gate | Evidence | Scope / limitation |
|---|---|---|
| AC-FR | [95-entry traceability map](fr_coverage.md), tests below | Test links identify executable coverage; they do not certify every possible gameplay branch. |
| AC-CMB | `test_sites_and_encounters.py`, `test_all_feats.py`, both ending campaigns | Production assignment/redo/round/aftermath and every ordinary feat route; registry audits preserve numeric tables. |
| AC-Economy | `properties/test_economy.py`, `test_post_domain.py`, paid-learning campaign | Deposit exemplar, caps, costs, kit rules and transactional rejection. |
| AC-QST | `test_campaigns.py`, `test_quest_gates.py`, `test_all_feats.py` | Both endings; key/infamy matrix; Wood absence; Voss tiers; Calling and counter-rites; encounter-free panel route. |
| AC-Persist | `test_post_domain.py`, `test_sites_and_encounters.py`, reset campaign, `test_saveio.py` | Slot round trips, corruption, autosave, backup, original/saved site and once-ever flags. |
| AC-Determinism | Four golden scripts, each replayed three times against RNG and event hashes | Linux replay evidence; cross-OS status is reported by the linked CI runs. Host-specific save paths excluded from canonical event hash. |
| AC-Presentation | `test_presentation.py`, bundled SDL smoke and exported frame | Layout, actual tcod key names, menu forms, legal feat lists, config and attract reel tested. Human window playthrough pending. |
| AC-Campaign | `golden_good.txt`, `golden_evil.txt` | Fresh-seed dispatch-only completion, score 100, both rewards and continuing play. |

Test files without a directory prefix above live in `tests/` or `tests/traces/`.
`advanced_training.txt` is a fresh-game command journey: recruitment, Tribunal
return, battles, XP division, paid training and learning. It contains no state
injection or privileged command. Both ending journeys use the documented Hollowed
Tribunal outcome through ordinary gameplay; this is disclosed rather than
presented as a balance test of six untouched level-one starters.

## Specification §16 checklist

| Rows | Implementation / evidence |
|---|---|
| §16.1 C-1–C-10 | Python 3.12/tcod; 120×40/8×16 font; keyboard menus; injected RNG; JSON slots; silent SFX_FLAG; layer/import tests; offline runtime; content vocabulary audits; autosave and post resume tests. |
| §16.2 OD-1–OD-8 | Canonical nouns/content; requested stack; transfer absent and single Filmon greeting; documented OQ/gap decisions; deterministic replay; canonical persistence; silent sound; complete data audits. |
| §16.3 | All 95 FR IDs mapped in fr_coverage.md. |
| §16.4 BR-1–13,30–37 | Training/body/economy/quest modules and registry audits; tests use dispatched commands and assert caps/invariants. BR-14–29 are absent from the source register. |
| §16.5 OQ-1–20 | Rules, feat matrix, starting tables and content registries; cost-curve, gate, Tribunal, rite and ending tests. See gap decisions for source contradictions. |
| §16.6 ADR-1–10 | Engine has no presentation/platform imports; single injected RNG; JSON content; lossless snapshot; capped credit; command playback; 27+3 roster; vacant53; removed transfer; silent toggle. |
| §16.7 counts | 182 items (corrected named-row arithmetic), 78 menaces, 58 feat rows including vacant53 and rites57/58, 17 posts, 8 rests, 11 sites, 15 strains, 6 professions, 9 skills, 4 standings. All map dimensions audited. |
| §16.8 | Public verb routing and content-reference audits; production commands only in gameplay fixtures; both endings reachable. Renderer remains behind frame contract. |

## Measured checks and release sign-off

Measured Linux CI result at implementation commit `1422a42`: **692 tests passed**,
**92.56% engine line coverage**, content audit, PyInstaller build and packaged SDL
smoke all passed ([job](https://github.com/playa77/wrath/actions/runs/41466657218/job/125349217430)).
Subsequent demo-persistence regression and portable-path/content checks passed
locally. The added explicit D-1/D-2 audit brings the suite to 693 cases.

A clean Python 3.12 environment installed only runtime/release dependencies;
`pip check` passed, followed by a fresh Linux one-folder build and SDL dummy-driver
boot/new/save/continue smoke.
The logical 960×640 frame was exported and inspected for readable glyphs/layout.

The CI workflow repeats tests, engine coverage ≥90%, build and packaged SDL smoke
on Linux, Windows and macOS and uploads each one-folder bundle. CI results must
be checked on [PR #3](https://github.com/playa77/wrath/pull/3/checks); configuring
the workflow is not evidence it has passed. An initial Windows run exposed Unix
path-string assumptions and CRLF checkout drift. Native Path comparisons and
`.gitattributes` now address both; the current CI run is the verification gate.

The v1.0.0 gate requires successful cross-OS CI replay/build/smoke (see live
checks), a human keyboard/window playthrough including the 60-second idle demo,
and final reviewer acceptance. Human playthrough and reviewer acceptance remain
outstanding. No v1.0.0 tag is created before those gates are evidenced.
