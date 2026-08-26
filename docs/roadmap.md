# Implementation Roadmap — *The Cradle Plateau: The Wrath of Doctor Voss*

This roadmap is the third document of the set ("Doc 3" per Doc 2 §2's file-ownership rule). It is a pure sequencing and allocation layer: it introduces **no new game values**. Every mechanic, number, string, and row comes from Doc 1 (design_document.md) or Doc 2 (technical_specification.md), cited per work package. The only roadmap-level decisions are listed in §0.3 and are closed — an agent that finds a value missing from Doc 1/Doc 2 and not covered by §0.3 must stop and flag it, not invent one.

## 0. Ground Rules

### 0.1 Authority & reading protocol

- Doc 1 = requirements, business rules, data schemas, OQ register. Doc 2 = project structure, data rows, module signatures, formulas, traces, acceptance tests.
- Before writing any code in a WP, the agent reads every section listed under that WP's **Authority**. Values tagged verbatim/anchor (BR tables, `[REQ]` strings, Doc 2 §5 tables) are **transcribed, never paraphrased**.
- Traceability: every test written names its anchor(s) (FR-ID, BR-ID, OQ-ID, TRACE-ID, or AC group) in a comment.

### 0.2 Global build invariants (binding on every WP)

1. **Determinism (C-3):** all randomness via injected `SeededRng` (`d100`/`dice`/`chance`/`pick` only). No `random` module, no wall-clock, no threads/async anywhere in engine (Doc 2 §9).
2. **Layering (C-6/ADR-1):** engine never imports from `ui/` or `render/`; no character/glyph literals in engine code; all content lives in `content/` JSON (ADR-3 — zero content constants in engine). Enforce with an import-direction lint test.
3. **Error taxonomy (Doc 2 §11):** rule rejections = `DomainError` → ERROR event, no state mutation; content faults = `ContentError` at load; save faults = `SaveError`; dev-only `InvariantBreach` compiled out in release.
4. **Tests rule (Doc 2 §12a, binding):** tests establish state **only by dispatching production commands** through `Engine.dispatch`. Hand-built game state in fixtures is a defect.
5. **File headers:** every source and data file carries a version header (`# Version: x.y.z | date`), bumped per change.
6. **No placeholders:** a WP is complete only when its Files list exists fully, its tests pass, and the full suite stays green.

### 0.3 Closed list of roadmap-level decisions [P-R]

- **P-R1** `engine/types.py` added to host the Doc 2 §8.1 type dictionary (enums + TypedDict DTOs). Same precedent as the spec's own addendum A1 (`platform/contentload.py`).
- **P-R2** Site map wall convention: site grids (Doc 2 §5.7) are authored as 30×24, default cell `wall`; carve listed room rects and corridors to `floor`; overlay listed doors/panels/traps/signs/levers. Each site ships with a pathfinding data-test asserting the entry reaches every scripted square.
- **P-R3** Rest-house integration: stepping onto a rest-house province square offers the rest flow (`infirmary.stay(resthouse=True)`, FR-WLD-004, $250+$25 tax), same as posts offer their menu.
- **P-R4** Menace-armor annex interpretation: Doc 2 §8.6 DAMAGE mixes id spaces; apply armor 4 to basalt colossus (#33), 6 to obsidian crawler, 3 to tyrant drake, 5 to tyrant king, 2 to high fiend and deeps fiend, 0 to all others. Encode with a code comment citing the mixed-space note and cover with a test.
- **P-R5** `ui/colors.py` exists per Doc 2 §8.4 though absent from the §2 tree (spec typo); assigned to WP-5.1.
- **P-R6** Demo orchestration: `session.demo` sets `phase=demo`; `app.py` detects it and feeds `demo_script.json` commands through the normal loop (ADR-6, seam A9). DomainError ⇒ silent return to boot menu (Doc 2 §5.10.4).

## 1. Phase Overview

| Phase | Name | Exit gate (all tests in addition to full suite green) |
|---|---|---|
| 0 | Scaffold & tooling | `pip install -e .[dev]` works; entry points exist; pytest runs |
| 1 | Contracts & platform primitives | RNG determinism + restart-equivalence tests; save file round-trip; loader fails fast on synthetic bad data |
| 2 | Content data layer | `cradle-content-check` green: §16.7 counts (180 / 78 / 56+2 / 17 / 8 / 11), anchor values byte-equal, string lint clean, referential integrity across registries |
| 3 | Engine core (post domain) | TRACE-01–05, TRACE-09 headless; deposit exemplar $999; OQ-4 spot values |
| 4 | World systems | TRACE-06–08, TRACE-10; AC-CMB assertions |
| 5 | Presentation layer | Composer six-region snapshot tests; every symbol id resolves; menu/verb lint green |
| 6 | Application assembly | Boot→menu→new→save→continue loop windowed; demo plays unattended; simcli hash reproducible |
| 7 | Verification campaigns | All four golden scripts pass with stable hashes ×3 runs (AC-Determinism, AC-Campaign); coverage ≥ 90 % engine lines; FR coverage map complete |
| 8 | Release | PyInstaller bundle smoke-tested per §13; §14 + §16 checklists audited and signed off |

WPs within a phase are listed in dependency order; each lists its predecessors.

---

## PHASE 0 — Scaffold & Tooling

**WP-0.1 — Repository scaffold** *(deps: none)*
Authority: Doc 2 §2, §3, §13. Files: `pyproject.toml`, `README.md`, full `src/cradle/` package tree (empty `__init__.py`s only), `deploy/pyinstaller.spec` (stub filled in Phase 8).
Build: project metadata with dependency pins exactly per Doc 2 §3 (Python 3.12.x, tcod >=16 <17); entry points `cradle` → `main:main`, `cradle-content-check` → `platform.contentload:check_main`; extras `[dev]` adding pytest.
Accept: `pip install -e .[dev]` succeeds on a clean venv; `pytest` collects and exits green.

**WP-0.2 — Test infrastructure** *(deps: 0.1)*
Authority: Doc 2 §12(a–b), §5.0 lint rules. Files: `tests/fixtures/lint_blocklist.txt`, `tests/conftest.py`, `tests/fixtures/README` fixtures dir.
Build: blocklist = C-8 lexemes (`magic, spell, god, divine, undead, zombie`) + C-9 period-rhetoric list; conftest provides tmp `CRADLE_HOME` save-dir fixture and seed fixtures. Harness `run_script` helper is deferred to WP-3.2 (it needs `Engine`).
Accept: fixtures importable; blocklist non-empty and loadable.

## PHASE 1 — Contracts & Platform Primitives

**WP-1.1 — Errors, types, config, paths** *(deps: 0.1)*
Authority: Doc 2 §8.1 (type dictionary), §11, §4. Files: `engine/errors.py`, `engine/types.py` (P-R1), `platform/config.py`.
Build: full §8.1 enum/DTO set; `resolve_paths(env)` with order `CRADLE_HOME` → OS user dir (stdlib-only) → `./userdata`, and subdirs `saves/`, `backups/`, `logs/`; `load_config`/`save_config` with defaults {window_scale 1, time_lag 4, sound true, debug false} and `CRADLE_DEBUG=1` override.
Accept: unit tests — bad JSON/missing keys in config fall back or raise per §11; path precedence honored.

**WP-1.2 — Events and frame contract** *(deps: 1.1)*
Authority: Doc 2 §6.2, §6.3, §8.3 `events`, §8.4 `frame`. Files: `engine/events.py`, `ui/frame.py`.
Build: closed Event kind set (`MSG, MENU, STATE, MAP, COMBAT, SFX_FLAG, SAVE_WRITTEN, ENDING, ERROR`), pure constructors; `Layer/Cell/Frame` types + `blank_frame()` at 120×40.
Accept: unit tests on constructors; events carry monotonically assigned `tick`.

**WP-1.3 — SeededRng** *(deps: 1.1)*
Authority: Doc 2 §8.3 `rng`, §10; Doc 1 ADR-2. Files: `engine/rng.py`.
Build: four draws; `DrawRec{tick, caller, dist, result}` log on every draw; `state()`/`restore()`; replay hash = SHA-256 over concatenated results.
Accept: same seed ⇒ identical sequences and log; `state()` snapshot → `restore()` ⇒ continuation identical; hash helper matches `simcli` needs (WP-6.3).

**WP-1.4 — Command registry** *(deps: 1.1)*
Authority: Doc 2 §6.1 (closed verb set), §8.3 `commands`. Files: `engine/commands.py`.
Build: `VERBS` table covering **every** §6.1 verb (session/utilities/chapter/advancement/post/trail/site/encounter/combat/meta) with legal phases and handler-path strings; `validate()` raising `DomainError` for unknown verbs or illegal phase. D-1 check: no transfer verb exists anywhere.
Accept: lint test asserting every verb in §6.1 is registered and every `menus.json` option (WP-2.10) and script menu resolves to a registered verb.

**WP-1.5 — Content loader** *(deps: 1.1, 0.2)*
Authority: Doc 2 §5.0, §8.2 `contentload`, §11. Files: `platform/contentload.py`.
Build: `load_all(root)` with §5.0 ordering (registries → world → scripts → text → presentation), header-envelope check, `ContentError(file, row, why)` naming offender; anchor-validation function (counts + anchor values) with hooks whose content assertions activate in Phase 2; `lint_strings(regs)` against the blocklist, honoring `"preserved": true` rows; `check_main()` entry point.
Accept: synthetic-registry unit tests (pass case + each failure class); boot-fail-fast behavior (non-zero exit, named file/row).

**WP-1.6 — Save I/O** *(deps: 1.1, 1.5)*
Authority: Doc 2 §6.4, §8.2 `saveio`; Doc 1 §7, §9 (slot layout). Files: `platform/saveio.py`.
Build: slots 0–4 (0 = autosave) under `saves/`; `write_slot`/`read_slot`/`list_slots`/`backup_member`/`restore_member`/`erase_all(confirm: True)`; filename sanitization to slot identifiers (path-traversal rejection, Doc 1 §7-3); structural validation on read (JSON parse, `schema_version`, required top-level §6.4 keys) → `SaveError` else. Full semantic `validate()` arrives with `engine/persistence.py` (WP-3.1); `saveio` must import and apply it at that point.
Accept: round-trip tests; corrupt file → `SaveError` with no partial state; traversal names rejected.

## PHASE 2 — Content Data Layer

Each WP here is transcription of Doc 2 §5 — values are normative as written. Every WP adds its data to `contentload`'s anchor validation and a `tests/test_content_*.py`.

**WP-2.1 — R-3: strains, professions, starting tables, XP constants** *(deps: 1.5)*
Authority: Doc 1 BR-1/2/3, OQ-2/3/9/20; Doc 2 §5.1. Files: `content/registries/strains.json`, `professions.json`, `starting_tables.json`, `xp_tables.json`.
Build: 15 strain rows incl. strange-strain addon fields {professions_allowed, fee_multiplier 1.5, impression_cha_delta −2, lodging annex}; 6 profession rows with 20-level HP tables (BR-1 + OQ-2 extension), interpolated MP tables (anchors per BR-2; round-to-nearest), attr mods, feat rates, start kits, standing weights; starting tables per OQ-20 **with CB Marksman stored as 15 + modifier +30 visible in data**; XP formula constants (engine evaluates the formula).
Accept: byte-equality tests vs BR-1/2/3 rows; interpolation spot checks; standing/credit/share tables match OQ-9/20.

**WP-2.2 — R-1: combat items** *(deps: 1.5)*
Authority: Doc 2 §5.2, §16.7; Doc 1 BR-8/9, §5.5. Files: `content/registries/items.json`.
Build: 100 identities (20 shields / 20 armor / 20 fire rungs with bow+rifle skin names / 40 melee) with **exactly** the names and value ladders listed; prereq rules per §5.2 (shields/armor str=v; fire str=dex=4+⌈4v/5⌉; melee 2×STR+DEX=10+v; elder flag ⇒ ⌈⅔⌉ prereqs); cost `25×v×(v+1)`.
Accept: count audit; anchor audit (Elder Lamellar v11; Elder Warbrand v25; named master-/sun-metal lines present).

**WP-2.3 — R-2: tonics, folio items, valuables** *(deps: 2.2)*
Authority: Doc 2 §5.3, OQ-12; Doc 1 BR-10/30. Files: `content/registries/tonics.json`, `folio_items.json`, `valuables.json`.
Build: radium 1–10 (HP n², BR-30 cure tiers I–IV), nerve 1–10 (3n MP), costs per §5.3; 20 folio identities (`folio_XVI {sealed:true}` with exact read message; 4 club-gazette curios); 40 valuables = 7 quest uniques (bound flags per BR-35) + `old_master_bow {mechanic: fire rung 19}` + 32 sellables at listed dollar values.
Accept: running audit items total = 180 (§16.7); tonic tier mapping tests.

**WP-2.4 — R-4: feats + feat matrix** *(deps: 1.5)*
Authority: Doc 1 §5.4 + ADR-8, OQ-1/5/13/17; Doc 2 §5.4. Files: `content/registries/feats.json`, `feat_matrix.json`.
Build: 58 rows from the Doc 1 §5.4 table (all `[REQ]` figures verbatim; Vitriol `[P]` dice 1–12/35/70/120; #53 `{vacant:true}`); matrix per Doc 2 §5.4 **with the four amended rows applied** (AM L8=[6,17,8], AM L13=[11,23,12], Doctor L14=[33,47,50], AM L15=[36,44,48,54]).
Accept: union-coverage audit = feats 1–52 plus 55/56 (53 excluded); anchors #5=1–10, #13=+50%/+15; Pugilist's Trance 2-quirk note present in row data.

**WP-2.5 — R-6: menaces + treasure tables** *(deps: 1.5)*
Authority: Doc 2 §5.5, §5.8; Doc 1 BR-12/32, OQ-8. Files: `content/registries/menaces.json`, treasure tables into `content/world/encounters_tables.json` (or registries per file map).
Build: all 78 rows as tabled; derive `band_min` from band grouping (1/2/3/4); map `t1…t8` notes to the treasure table; caster rows carry `feats` (one offense line + one control) and `cast_budget` 2/3/4/5 per tier; mummified flags exactly on {25, 26, 39, 54, 55, 76, 77, 78}.
Accept: audits — 78 rows; all XP ≤ 65,535 (BR-12); all FR-CMB-008 caster types present (27, 34, 35, 37, 38, 56, 57); unique-boss set per BR-32 present, incl. both Voss forms.

**WP-2.6 — R-7: world maps + encounter tables** *(deps: 2.5)*
Authority: Doc 2 §5.6, §5.8; Doc 1 BR-33, OQ-19. Files: `content/world/province.json`, `ziggurat_sun.json`, `ziggurat_drowned.json`, `deeps.json`, `encounters_tables.json`.
Build: province 75×50 generated programmatically (a one-off `tools/gen_province.py` committed alongside is permitted per file-ownership extension) from default `trail` + overlay rects/polyline in §5.6.1 order + escarpment border ring; all 17 posts, 8 rest-houses (Royal Rest canonical), and 9 province-anchored sites at the exact coordinates tabled; ziggurat maps 18×9 per §5.6.2 with planar posts and features; deeps 30×15 with the eight lava rects; encounter rate table 1/12, 1/10, 1/8, 1/6, 0 (river) and per-terrain pools exactly per §5.8; night-camp rule every 10th trail move, ambush 1/3.
Accept: data tests — dimensions, sector math (A–E=15 cols, I–V=10 rows), band rule `1+max(|col−C|,|row−III|)`, feature coordinate assertions, deeps safe-lane existence check.

**WP-2.7 — R-8: site scripts D1–D5** *(deps: 2.3, 2.4, 2.5, 2.6)*
Authority: Doc 2 §5.7.1–5.7.5, §6.5; Doc 1 FR-DGN-001…006, FR-QST-002…014, BR-34/35/36, OQ-16. Files: `content/world/sites/site01…site05*.json`, `content/world/scripts/site01…05.json`.
Build: 30×24 grids per P-R2; transcribe every room, door (incl. unpickable `lk` semantics), panel, trap, set composition, stash, script square, and menu verbatim from the §5.7 DSL blocks. Honor inline OQ-16 fixes (lever dead-beast rule, once-ever wrestling flag, dedup).
Accept: referential integrity tests (every menace/item/feat/DLG id referenced exists); per-site reachability test (P-R2); DSL verb closure test — only §6.5 verbs used.

**WP-2.8 — R-8: site scripts D6–D11** *(deps: 2.7)*
Authority: Doc 2 §5.7.6–5.7.11; Doc 1 FR-QST-015…025, OQ-7/10. Files: `site06…site11` map + script JSONs.
Build: as WP-2.7, plus: Drowned gate matrix (infamy tiers vs key), mirror layout of site06, wrong-arch 80-damage squares, plinth cipher structure (27 fixed decoded words DLG-066; filler drawn from closed 24-word STR-C1 list), glyph-circle 7-option menu with option 4 → `transport deeps(15,7)` + consume resonator, Wood audience infamy≥1 → "There is no one here.", fastness panel route avoiding all five sets, climax branch menu, hermit bowls (max 2 ever, once-ever flag), drake rings + Boo Boo Kitty vault.
Accept: as WP-2.7, plus gate-condition unit data tests (infamy thresholds 0/1–2/≥3).

**WP-2.9 — Text registries** *(deps: 0.2, 2.7, 2.8)*
Authority: Doc 2 §5.9; Doc 1 §11 notes 3–4, C-8/C-9, RS-7/RS-8. Files: `content/text/folios.json`, `dialogue.json`, `strings.json`, `color_tokens.json`.
Build: folio payload map table verbatim; **author** the 15 folio payload texts (40–90 words each) strictly from the normative beat lists, canonical nouns; dialogue rows: `[REQ]`/preserved strings byte-exact (DLG-001, DLG-020, DLG-044, DLG-061, DLG-066, DLG-070, DLG-080–082, DLG-085–087, DLG-090, SYS strings incl. "MENACE APPROACHES", "$" messages, exemplar rating band text), others authored to beats; color-text registry rows per §5.9.3; color token RGB table per §5.10.1.
Accept: lint pass clean (blocklist + C-9); preserved-string equality tests; every DLG id referenced by site scripts exists.

**WP-2.10 — Presentation registries** *(deps: 1.4, 2.9)*
Authority: Doc 2 §5.10.2–5.10.4, §5.10.1; Doc 1 §6.2, FR-UIX-001/002/003, ADR-6. Files: `content/presentation/symbols.json`, `menus.json`, `demo_script.json`.
Build: full symbol dictionary with ids **exactly** as tabled (256–402, preserving the §5.10.2 id-ordering quirks and state variants incl. mummified→ash for +M rows); all menu descriptors per §5.10.3 resolving only to §6.1 verbs; demo script per §5.10.4 (fixed seed 7 command sequence).
Accept: id-uniqueness audit; menace ids 325–402 map 1:1 to §5.5 row order; WP-1.4 verb lint green against menus; six-region layout metadata present.

**Phase 2 gate:** `cradle-content-check` passes the full §16.7 audit + lint + referential integrity.

## PHASE 3 — Engine Core (Post Domain)

**WP-3.1 — GameState + persistence** *(deps: 1.x all, Phase 2 gate)*
Authority: Doc 2 §8.1 DTOs, §8.3 `state`/`persistence`, §6.4; Doc 1 BR-7/8/36, FR-SES-001, ADR-4. Files: `engine/state.py`, `engine/persistence.py`, `tests/test_state.py`.
Build: `new_game(seed)` (Terminus #1, `phase=post`, empty expedition, automata slots 28–30); `check_invariants` (dev-flagged); `project()` projection type; `snapshot`/`restore` (rng_state carried separately); `site_snapshot`/`site_restore`; full §6.4 `validate` wired into saveio.
Accept: round-trip snapshot→restore equivalence (state + rng); invariant trip tests; `SaveError` range cases.

**WP-3.2 — Engine core + session verbs + test harness** *(deps: 3.1)*
Authority: Doc 2 §8.3 `core`, §15.1 A2 addendum; Doc 1 FR-SES-001/002, FR-SAV-001/004, C-10. Files: `engine/core.py`, `tests/harness.py`.
Build: `Engine.__init__(state, rng, regs, save_sink, read_sink, backup_sink, restore_sink, erase_sink)` per A2; `dispatch` pipeline (validate→route→handler→dev invariants→events); session verbs incl. `session.new` (→ `new_game` + `creation.starter_six` + autosave slot 0), `session.continue/save`, `core.autosave`; `tests/harness.py run_script(verbs, seed)` helper that only dispatches production commands (§12a).
Accept: TRACE-01 headless portion; quit-mid-field → continue resumes at last post (TRACE-12 subset); corrupt-slot behavior.

**WP-3.3 — Creation + roster** *(deps: 3.2)*
Authority: Doc 2 §8.3 `creation`/`roster`; Doc 1 FR-CHR-001…008, BR-3, OQ-15, C-9; Doc 2 §5.1. Files: `engine/creation.py`, `engine/roster.py`.
Build: recruit flow (begin → strain pick with "STRANGE" random selection → profession gating charter 6 / strange {White Hunter, Cat Burglar} → roll → accept/reject); standing weights charter {10/40/35/15}, strange {30/45/20/5} `[P]`; strange penalties per C-9 framing fields; `starter_six` fixed six in slots 1–6 on all builds; list/purge (permanent)/add (resident gate, <6)/drop/rename/designate-automaton (no slot consumed).
Accept: TRACE-02/03 headless; BR-3 caps enforced; roster bound 27+3.

**WP-3.4 — Training & advancement** *(deps: 3.2)*
Authority: Doc 1 FR-ADV-001…005, BR-1/2/4/5/6, OQ-2/3/4/5; Doc 2 §8.3 `training`. Files: `engine/training.py`.
Build: `train` (XP threshold `⌊500×n×S×P×A⌉`, cost `⌊200×L×((21−CHA)/10)×(1+0.05×trainings)⌋` from treasury; HP per table + CON ±5%/point adjustment floor; award `100×L×shares`; `trainings_taken += 3` after skill phase); `train_skill` ×3 with +8/+4/+2 diminishing repeats `[P]`, cap 250; `learn_feat` (matrix row, slots `rate×level+max(0,INT−10)`, cost `150×mp×((21−CHA)/10)`; "can learn no new feats at this time" branch); `mp_growth` (25% +1 max iff `spent_mp`, ≤ table ceiling); `divide_xp` on post arrival (living members, floor, remainder discarded).
Accept: TRACE-09; OQ-4 spot values $3,520 and $17,550; AC-Economy assertions.

**WP-3.5 — Credit desk** *(deps: 3.2)*
Authority: Doc 1 FR-TWN-001, BR-7, OQ-9, ADR-5; Doc 2 §8.3 `credit`. Files: `engine/credit.py`.
Build: withdraw/deposit with ceilings ≤ $65,000 both sides; fee $1×expedition members `[P]`; apportion by standing shares 1/2/2/3, each lot floored; overflow rejected as DomainError, no mutation.
Accept: TRACE-04 — the $6,000/6 ⇒ $999 exemplar is a named test; no-op and overflow branches.

**WP-3.6 — Outfitter** *(deps: 3.2)*
Authority: Doc 1 FR-TWN-002, BR-8/9; Doc 2 §8.3 `outfitter`. Files: `engine/outfitter.py`.
Build: per-visit stock regeneration by band tier with folio/curio persistence once stocked (weapons/tonics restock+vary); 12-row pages with unusable flags from prereq eval; buy (treasury debit, kit ≤9, exact "You can't afford that" and kit-full branches); fire-rung bow/rifle subchoice on buy; sell at ⌊cost/2⌋.
Accept: TRACE-05; BR-9 unusable-flag matrix incl. elder discount.

**WP-3.7 — Infirmary + timekeep** *(deps: 3.4)*
Authority: Doc 1 FR-TWN-004, FR-WLD-004, FR-BOD-003/006, OQ-6; Doc 2 §8.3 `infirmary`/`timekeep`. Files: `engine/infirmary.py`, `engine/timekeep.py`.
Build: `stay(resthouse)` ($250+$25 tax, refuse if unaffordable; full HP/MP; cure 1 Broken or 2 Injured in vital order head→torso→arm_r→arm_l→leg_r→leg_l; `mp_growth` hook; +7 days); `advance(days)` with aging marks 50/70/90% of strain lifespan, each applied once (flagged): −1/−2/−3 STR/DEX/CON cumulative, INT/CHA −1 at 90%; move-cost table (trail 1, badlands 1, swamp 2, escarpment 3, river +1; camp 1; stay 7; site leg 1 day/10 moves min 1).
Accept: aging-crossing tests (attribute deltas, once-only marks); rest-house debit/refusal.

**Phase 3 gate:** TRACE-01–05 and TRACE-09 green headlessly.

## PHASE 4 — World Systems

**WP-4.1 — Body** *(deps: 3.x)*
Authority: Doc 1 FR-BOD-001…003, BR-30/31; Doc 2 §8.3 `body`, §8.6 BODY thresholds + TRAP_FX. Files: `engine/body.py`.
Build: six areas, severity escalation per `[P]` thresholds (≥1 Injured, ≥25% Broken, ≥50% Gone of max HP); death at hp≤0 or head/torso Gone; status derivation (Down ≤25%, menace Unconscious ≤5%); `cure` BR-30 tiers most-vital-first; sleeping wake rules (50% on damage, 1d4 rounds, #51).
Accept: unit matrix over thresholds; death rules; cure-order tests.

**WP-4.2 — Feats** *(deps: 4.1)*
Authority: Doc 1 FR-MAG-001…005, BR-37, §5.4, OQ-1/8/13/17; Doc 2 §8.3 `feats`, §8.6 FEAT_FX + AUTOMATA. Files: `engine/feats.py`.
Build: domain checks per phase; MP debit; every effect family (cures/Lancet/Sweep/Assault/Vitriol, passives #13–17 loads/trance, #18–21 surge incl. Slow-counter, #22–25 hardening, #26–28 charm/sleep/dread, progressive Confusion/Enervation/Paralysis supersede rules, #43 Egress, #44 Revivification 75% + CON −1..2, #48 automaton summon/depart/no-XP-share, #49 60/40 mummified-only, #51 Awaken, #52 15% misreport-adjacent-tier, #54 17-post cross-planar menu, #55/56 with the stronger-at-lower-MP quirk preserved, #57 script-gated, #58 full-party heal + infirmary-strength cure); vacant #53 rejected; right-arm rule gating; `counter_passive` (OQ-8 inverse).
Accept: one test family per effect row (§12 coverage floor); BR-37 interaction tests (Dread stacks, Sleep no-deepen, passive-counters-active).

**WP-4.3 — Quests + tribunal** *(deps: 3.2)*
Authority: Doc 1 FR-QST global + 020/023, FR-BOD-004/005, OQ-7/11/18; Doc 2 §8.3 `quests`/`tribunal`, §8.6 SCORE_W. Files: `engine/quests.py`, `engine/tribunal.py`.
Build: Filmon spine briefs 1–6 in enforced order with DLG-002 prefix / DLG-001 greeting; `add_infamy` + tiers 0 / 1–2 / ≥3 (acts: statue +1 each ×3, shrine destroy +2 — nothing else logs); `update_score` weights summing exactly 100 + rating bands (43→"average" exemplar string); `end_game` both kinds with OQ-18 awards ($20,000 treasury with overflow-forfeit message, +50,000 XP per survivor, elder-work melee per member for good / Obsidian Regalia + urn-shard curio for evil), flags, play-continues; `tribunal.judge` formula with clamps, Returned (50% HP `[P]`, treasury→0, CON−1) vs Hollowed (level 20, frozen, irreversible) then transport to post context.
Accept: score-weight sum test; rating boundary tests; TRACE-10 both outcomes + Hollowed training-refusal.

**WP-4.4 — Encounters** *(deps: 4.1, 4.2)*
Authority: Doc 1 FR-ENC-001…008; Doc 2 §5.8, §8.3 `encounters`, OQ-8/19. Files: `engine/encounters.py`.
Build: approach sequence ("MENACE APPROACHES" + identity/ranks/statuses) re-shown after every round; five options with exact `[P]` probabilities — parley by disposition (50/25/0), beg-mercy (60% if Σparty hp ≤ Σfoe hp else 25%) taking all treasury + ≤3 found items, flee 50% with free-attacks failure; surrender at ≥50% killed; random warden (rate table, `band_min ≤ band` filter, uniques excluded); ambush with `sleep_start`; morale at ≥60% losses, P(flee) 40% (Savage 10%).
Accept: TRACE-07 alternate-exit branches; disposition/morale probability tests by seeded streaks.

**WP-4.5 — Combat** *(deps: 4.1–4.4)*
Authority: Doc 1 FR-CMB-001…008, FR-BOD-002, BR-13; Doc 2 §8.3 `combat`, §8.6 RESOLUTION/DAMAGE/BALLISTICS + P-R4. Files: `engine/combat.py`.
Build: per-member assignment with legality gates (broken any-limb ⇒ no Fire; right arm Broken/Gone ⇒ Parry only — exactly per FR-BOD-002); documented fallbacks (FR-CMB-002) logged; `redo` only after all assigned; run_round order, tactics per RESOLUTION, `pos_mod` formula (uniform ranks ⇒ 0), ballistics row selection (fire/aim/hand/tall; feats uniform), foe 50% cast-vs-melee within budget (mesmerist ⇒ `counter_passive`), morale handoff; `aftermath` — XP to leg ledger + dollars to treasury immediately (cap-forfeit message), trail auto-treasure to found_items ≤90 unusable-until-distributed, in-site Find Item path; defeat ⇒ tribunal.
Accept: full AC-CMB battery; TRACE-07; reach rules (CB any rank, WH Lunge rank≤2); auto-hit Sleeping; found-item cap.

**WP-4.6 — Trail** *(deps: 3.7, 4.4, 4.5)*
Authority: Doc 1 FR-WLD-001…006; Doc 2 §8.3 `trail`, §5.6/5.8, OQ-6/19. Files: `engine/trail.py`.
Build: N/S/E/W movement; terrain gates (escarpment/open water blocked); river per-member Swim roll ⇒ 2d10 drowning torso on failure, zero encounters on water; terrain-warden rolls per move; every-10th-move night camp with sentry Listen; `camp_rest` voluntary; rest-house arrival per P-R3; site-square enter prompt; post arrival ⇒ `divide_xp` + phase=post + autosave; `perform` (Field/Everywhere feats), `use_tonic` (BR-10), `inspect` summary.
Accept: TRACE-06; OQ-19 rate table honored; sleep-start ambush chain.

**WP-4.7 — Sites + script interpreter** *(deps: 4.2–4.6, Phase 2 gate)*
Authority: Doc 1 FR-DGN-001…006, BR-34/35/36; Doc 2 §8.3 `sites`/`scripts`, §5.7, §6.5. Files: `engine/sites.py`, `engine/scripts.py`.
Build: enter with saved/original choice and BR-36 one-time-flag immunity; movement with wall thud, hidden panels (no signal), door auto-Listen with warn/retreat, locks incl. unpickable strings, trap trigger/disarm (exactly one member; failure ⇒ TRAP_FX); `look` ray-LOS radius 3, walls block; 1/12 menace roll per move; leg time-billing; `exit(save_state)` snapshot flow; DSL interpreter for the closed §6.5 action vocabulary incl. gate evaluation (flags, items, infamy tier, strain-present, once-flags) and menu suspension/resume via `script_ctx`.
Accept: TRACE-08 (incl. restore-original keeps one-time flags), shrine grant-once + later-gold, chute once-ever; every scripted outcome in §5.7 reachable via tests.

**Phase 4 gate:** TRACE-06–10 green; AC-CMB green.

## PHASE 5 — Presentation Layer

**WP-5.1 — Symbol map + colors** *(deps: 2.9, 2.10)*
Authority: Doc 2 §8.4 `symbolmap`/`colors`, §5.10.1/2; P-R5. Files: `ui/symbolmap.py`, `ui/colors.py`.
Build: id<256 CP437 passthrough; ≥256 dictionary resolution with state-variant overrides; token→RGB with `ContentError` on unknowns.
Accept: every entity id used in content resolves; state variants (mummified, sleeping, dead, hollowed) verified.

**WP-5.2 — Composer** *(deps: 5.1, 3.1)*
Authority: Doc 1 FR-UIX-001; Doc 2 §8.4 `composer`. Files: `ui/composer.py`.
Build: six regions with exact constants (member panel rows 0–11; messages 12–23 cols 0–59; menace ranks 12–23 cols 60–119; area map 24–39 cols 0–55; menu 24–39 cols 56–87; figures 24–39 cols 88–119); province viewport always fully mapped vs site explored-only; K/S/U/D foe status letters; six-glyph body diagrams; consumes projection+events only (C-6).
Accept: snapshot tests per phase context (post/trail/encounter/combat/site); AC-Presentation gates.

**WP-5.3 — Menu kit + input map** *(deps: 1.4, 2.10)*
Authority: Doc 1 FR-UIX-002; Doc 2 §8.4 `menukit`/`inputmap`, §5.10.3. Files: `ui/menukit.py`, `ui/inputmap.py`.
Build: descriptor interpreter → `Command` (digits, bracket letters, first-letter two-choice, Y/N, ENTER continue, ESC where Leave exists); dynamic paging for shop/stock; arrows + numeric-pad and 3-E-S-W diamond fallback; column numbers 1–6.
Accept: every descriptor drivable by synthetic key streams; FR-UIX-002 coverage tests.

**WP-5.4 — Text renderer + tile interface** *(deps: 5.1)*
Authority: Doc 1 C-1/C-2, ADR-1; Doc 2 §8.5. Files: `render/text_renderer.py`, `render/tile_iface.py`.
Build: tcod window 120×40, CP437 font, integer scale from config (960×640 base); layer-ordered blit; keyboard-only poll; `RendererProtocol` interface-only.
Accept: windowed smoke (manual, recorded — SDL cannot be headless-verified in CI; state this honestly in the WP report); protocol import test.

## PHASE 6 — Application Assembly

**WP-6.1 — App loop + clock + demo** *(deps: 5.x, 4.x)*
Authority: Doc 2 §8.2 `app`/`clock`, §9, ADR-6; Doc 1 §9. Files: `platform/app.py`, `platform/clock.py`.
Build: cycle poll→translate→handle_key→dispatch→compose→render→pace; `pace = time_lag×150ms×n_msgs`; 60s idle ⇒ `session.demo` feeding `demo_script.json` per P-R6; quit-to-menu; top-level exception guard (debug-logged, exit; recovery via Continue).
Accept: scripted-loop tests with fake renderer (time-lag 0 vs 9 measurably changes pacing — AC-Presentation); demo completes unattended.

**WP-6.2 — Composition root** *(deps: 6.1)*
Authority: Doc 2 §15.1 exact nine-step sequence. Files: `src/cradle/main.py`.
Build: literally the §15.1 steps and nothing else; sole infrastructure constructor.
Accept: static lint asserting no other module constructs `SeededRng`/`Engine`/`TextRenderer`/sinks.

**WP-6.3 — Headless driver** *(deps: 3.2, 6.1 minus renderer)*
Authority: Doc 2 §8.2 `simcli`, §12. Files: `src/cradle/simcli.py`.
Build: `run_script(path, seed, hash_only)` — one verb per line (`verb {json-args}`), `#` comments; identical object graph as main but temp-dir sinks, no renderer; returns summary + SHA-256 of draw log; CLI `python -m cradle.simcli script.txt --seed N --hash`.
Accept: TRACE-12 determinism assertion (3 runs, identical hash).

## PHASE 7 — Verification Campaigns

**WP-7.1 — Trace & spec test battery** *(deps: Phase 6)*
Authority: Doc 2 §14, §15.2. Files: `tests/traces/test_trace01…12.py`, plus AC-Economy/AC-CMB suites.
Build: each TRACE as a scripted test using `tests/harness.py` only; the exact branch matrix for Drowned gate (pure/stained/blackened × key, OQ-7), Wood absence at infamy ≥1, Voss talk tiers, feat refusals (DLG-083/084), #57-only ether-gate, #49 effectiveness vs Hollowed Voss, once-ever flags (Kilmor→bloodstain, hermit bowls, wrestling CON), fastness panel route with zero combat encounters.
Accept: all trace tests green; every branch name-listed in §14 mapped.

**WP-7.2 — Golden campaigns** *(deps: 7.1)*
Authority: Doc 2 §12, §14 AC-Determinism/AC-Campaign, TRACE-11 assertion list. Files: `tests/golden/golden_good.txt`, `golden_evil.txt`, `golden_tribunal.txt`, `golden_site_reset.txt` + assertions.
Build: dispatch-only command scripts, one fixed seed each, segmented per TRACE-11 (orientation→D1→D2→funeral→infamy/stats→Enclave→funicular→ziggurats→cipher→circle→Deeps→War-Camp→Fastness→climax→ending), final-state assertions (score=100, ending flags, play-continues invariants) + replay hashes; site-reset campaign asserts BR-36 under restore-original; tribunal campaign forces wipe and covers both outcomes.
Accept: hash stable across 3 runs per script (record cross-OS validation as a CI/manual step); zero hand-built state (§12a audit).

**WP-7.3 — Properties & coverage audit** *(deps: 7.1)*
Authority: Doc 2 §12 properties layer, coverage floor. Files: `tests/properties/…`, coverage config.
Build: generation-based property tests (BR-7/BR-8 ceilings never exceeded; XP divide conserves total; one-time flags monotonic); FR-coverage report mapping every FR-ID (95/95 as amended by D-1) to ≥1 test; engine line coverage ≥ 90%; D-1 absence checks (no transfer verb; single greeting); D-2 functional-silent assertion (SFX_FLAG emitted, no audio device referenced anywhere).

## PHASE 8 — Release

**WP-8.1 — Packaging** *(deps: Phase 7 gate)*
Authority: Doc 2 §13, A-4; Doc 1 §8. Files: `deploy/pyinstaller.spec` (complete), packaging README section.
Build: one-folder bundle per OS; fonts + `content/` bundled via `datas`; version string from pyproject echoed into config; post-package smoke procedure: boot → 60s demo auto-play → new game → save/continue round-trip. Record result; packaging is the least automatable step — report exactly what was manually verified.

**WP-8.2 — Final audit & documentation** *(deps: 8.1)*
Authority: Doc 2 §14 + §16 in full.
Build: walk every §14 AC group and every §16 table row producing a signed checklist with test evidence links; run §16.7 count audits; update README (build/run/test/package instructions); tag v1.0.0.

## 2. File → WP Ownership Map (completeness check vs Doc 2 §2)

- **Scaffold:** pyproject/README/spec (0.1, 8.1), tests fixtures (0.2, 3.2, 7.x).
- **Engine:** errors/types (1.1), events/frame (1.2), rng (1.3), commands (1.4), state/persistence (3.1), core (3.2), creation/roster (3.3), training (3.4), credit (3.5), outfitter (3.6), infirmary/timekeep (3.7), body (4.1), feats (4.2), quests/tribunal (4.3), encounters (4.4), combat (4.5), trail (4.6), sites/scripts (4.7).
- **Content:** registries (2.1–2.5), world+encounters (2.6), sites+scripts (2.7–2.8), text (2.9), presentation (2.10).
- **UI/render:** symbolmap/colors (5.1), composer (5.2), menukit/inputmap (5.3), text_renderer/tile_iface (5.4).
- **Platform:** config/paths (1.1), contentload (1.5), saveio (1.6), app/clock (6.1), main (6.2), simcli (6.3), deploy (8.1).

Every path in Doc 2 §2 is owned exactly once; the only additions are `engine/types.py` (P-R1), `ui/colors.py` (P-R5, spec-named), and optional `tools/gen_province.py`.

## 3. Dependency Notes / Critical Path

Critical path: 0.1 → 1.1 → 1.5 → 2.1 → 2.5 → 2.6 → 2.7/2.8 → 3.1 → 3.2 → 4.6/4.7 → 6.1 → 7.2. WP-2.x content WPs after 2.1 are accuracy-transcription heavy but independent of engine code; they can be built while engine WPs proceed only if Phase 1 is complete (loader + lint needed for gates). Never reorder Phase 2 after Phase 3 partially — engine tests dispatch against real registries from WP-3.1 onward.

## 4. Risk Register (from Doc 1 §11, mapped)

- **R-1 balance divergence** → anchor byte-equality tests in Phase 2; AC-Economy/AC-CMB replay assertions in Phase 7.
- **R-2 cross-doc inconsistency** → Phase 2 gate runs the §16.7 audit; known spec seams already fixed by addenda A1/A2 and P-R4/P-R5 listed above.
- **R-3 content volume** → content split across six WPs (2.1–2.10) with per-file acceptance so transcription defects surface early.
- **R-4 funeral/Tribunal/infamy cross-save interactions** → dedicated TRACE-10/11 branch tests + `golden_site_reset` + BR-36 monotonicity property.

## 5. Final Acceptance

The project is done when WP-8.2's signed checklist shows: §14 items AC-FR (95/95 incl. D-1 absences, D-2 silent-functional), AC-CMB, AC-Economy, AC-QST, AC-Persist, AC-Determinism, AC-Presentation, AC-Campaign — all evidenced — and §16.1–16.8 walkthrough complete. Manual-only verifications (SDL window smoke, PyInstaller run, cross-OS hash runs) are recorded as such, never claimed as automated.