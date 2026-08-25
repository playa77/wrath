# TECHNICAL SPECIFICATION

**Title:** *The Cradle Plateau: The Wrath of Doctor Voss* — Technical Specification
**Version:** 1.0.0 · **Date:** 2025-06-13 · **Status:** Draft
**Upstream authority:** Document 1 — Design Document, v1.0.0 (all sections). Constraint register C-1…C-10 (Doc 1 §2.1), deviations D-1/D-2 (Doc 1 §2.6), decisions ADR-1…10 + OQ register (Doc 1 §10) bind every section below.

## Revision History

| Version | Date | Status | Changes |
|---|---|---|---|
| 1.0.0 | 2025-06-13 | Draft | Initial delivery. |

**Delivery plan.** Length is dictated by SC-1 (Doc 1 §0): this document is delivered in three installments in template order where practical — **(I)** §§1–4, 6–14; **(II)** §5 Data Layer (exhaustive registries); **(III)** §8 Module Specifications, §15 Seam Register & Call Traces, §16 Final Consistency Checklist. Final assembled order follows the template 1–16. Trace IDs (`TRACE-01…`) defined in §14 are honored verbatim in §15.

---

## 1. Implementation Scope

**In scope (each traceable):** the complete single-player build described by Doc 1 §2.2 (all 95 FR entries as amended by D-1), §2.3 business rules, §2.5 NFRs, §2.4 registries R-1…R-8 with 100% row closure (this document §5), the three-layer architecture (Doc 1 §3) with text renderer, deterministic engine (OD-5), JSON save system (OD-6), demo reel (A-1), utilities incl. backup/restore (FR-SAV-003), and packaging (A-4).

**Out of scope (non-goals, Doc 1 §1):** tile renderer *implementation* (its interface seam is specified, §8 `render.tile_iface`, and stubbed for tests only); pointer input; audio output (toggle ships silent, D-2); multiplayer/network; modding tools; save migration code; veteran transfer (D-1); difficulty settings; third-party anything.

## 2. Project Structure

Repo root `cradle/`:

```
pyproject.toml            # build metadata, entry point `cradle`
README.md
src/cradle/
  main.py                 # COMPOSITION ROOT (only module constructing infrastructure)
  engine/
    core.py               # Engine facade: dispatch(), state access, tick counter
    state.py              # GameState aggregate + invariant checks (dev asserts)
    rng.py                # SeededRng port: draw log, snapshot/restore
    commands.py           # Command types + verb registry (§6.1)
    events.py             # Event types (§6.2)
    roster.py  creation.py  training.py  credit.py  outfitter.py  infirmary.py
    timekeep.py           # calendar + aging (OQ-6 tables)
    trail.py              # overworld movement, terrain, camps, rest-houses
    sites.py              # doors/locks/listen, panels, traps, look, exits, site-state
    scripts.py            # R-8 script-DSL interpreter
    encounters.py         # contact sequence, warden for random menaces, morale
    combat.py             # rounds, tactics, fallbacks, ballistics, statuses, spoils
    feats.py              # registry-driven effects + interaction classes (BR-37)
    body.py               # locations, severities, healing tiers, death rules
    quests.py             # Filmon spine, infamy, gating, endings, tribunal hook
    tribunal.py
    persistence.py        # snapshot -> SaveDoc DTO and back (pure, no files)
    errors.py             # DomainError taxonomy (§11)
  content/                # DATA ONLY (installed as package data; §5)
    registries/  items.json tonics.json folio_items.json valuables.json
                 strains.json professions.json feats.json feat_matrix.json
                 menaces.json xp_tables.json starting_tables.json
    world/  province.json ziggurat_sun.json ziggurat_drowned.json deeps.json
            sites/site01_maproom.json … site11_drakehollows.json
            scripts/site01.json … site11.json encounters_tables.json
    text/  folios.json dialogue.json strings.json color_tokens.json
    presentation/  symbols.json menus.json demo_script.json
  ui/
    frame.py              # Cell/Layer/Frame types (§6.3)
    composer.py           # region layout per FR-UIX-001 (§8)
    symbolmap.py          # symbol_id resolution + state variants
    menukit.py            # descriptor interpreter → Command
    inputmap.py           # FR-UIX-002 key bindings
  render/
    text_renderer.py      # python-tcod blit + keyboard poll
    tile_iface.py         # future renderer protocol (stub; swap contract)
  platform/
    app.py                # game loop: input → menukit → engine → composer → render
    saveio.py             # slot files, autosave, backup/restore, schema validation
    config.py             # config.json load/save (§4)
    clock.py              # frame pacing + time-lag implementation
  simcli.py               # headless driver: run script file → event log / hash
tests/                    # §12
deploy/pyinstaller.spec
```

**File-ownership rule:** `content/` may be read by any module at load time but written by nothing at runtime (except future content tooling, out of scope). Every path above is created/maintained by exactly one Doc 3 work package (mapped in Doc 3 §6).

## 3. Dependencies

| Dependency | Version | Role | When |
|---|---|---|---|
| Python | == 3.12.x | runtime | always — C-1 |
| `tcod` (python-tcod) | >= 16, < 17 pinned at `pyproject` lock | SDL window console, CP437 fonts | runtime — C-1 |
| `pytest` | >= 8 | test runner | dev |
| `pyinstaller` | >= 6 | packaging | release only — A-4 |

No other runtime dependencies (stdlib only beyond tcod) — C-7/SC-1 auditability. No network fetch at build or runtime after `pip install` (C-7). Type/linters optional, non-gating.

## 4. Configuration

`config.json` (user-writable; lives beside save dir, §4.2): `{window_scale: 1..3 (default 1 → 960×640 per C-1), time_lag: 0..9 (default 4 [OQ-flagged P, Doc 1 §9]), sound: bool (default true; FUNCTIONAL-SILENT: honored in event flags, no audio emitted — D-2), debug: bool (default false; env CRADLE_DEBUG=1 overrides)}`.

**Paths resolution order:** `CRADLE_HOME` env → OS-appropriate user dir (platformdirs-style, implemented inline, stdlib only) → `./userdata` fallback. Subdirs: `saves/slot0.json` (autosave), `saves/slot1..4.json` (manual), `backups/` (member export files per §6.5), `logs/debug.log` (opt-in). Content pack path frozen at install; read-only. Slot layout = Doc 1 §9 [P] register, unchanged.

## 5. Data Layer

### 5.0 Conventions, file↔table map, validation

- All registry files are UTF-8 JSON with header `{ "registry": "<name>", "schema_version": 1, "rows": [ … ] }`. Load order at boot (fail-fast, §11 `ContentError`): registries → world → scripts → text → presentation.
- **Anchor validation** (runs in `cradle-content-check` and §12 content tests): counts — items 180, folio identities 20, menaces 78, feats 56 slots (#53 vacant) + rites 57/58, posts 17, rest-houses 8, sites 11; values — BR-1/BR-2/BR-3/BR-30 rows byte-equal; feat #5 dice `1d10`, #13 `+50%/+15` (Doc 1 R-4 anchors); FR-UIX-001 six regions present in `menus.json`.
- **String lint (C-8/C-9):** forbidden lexemes in any `text/` or `presentation/` string: `magic, spell, god, divine, undead, zombie` (+ period-rhetoric blocklist per C-9, exact list in `tests/fixtures/lint_blocklist.txt`). Allowed legacy terms appear only inside quoted preserved strings flagged `"preserved": true`.
- Attribute/skill/feat/menace references are by integer ID everywhere (names live in exactly one row).

### 5.1 R-3 — `strains.json`, `professions.json`, `starting_tables.json`

`strains.json`: 15 rows `{id, name, kind: charter|strange, str_cap…cha_cap, lifespan_years, decline_marks:[.5,.7,.9]}` — maxima/lifespans byte-equal to Doc 1 §2.3 BR-3 / FR-BOD-006. `strange` rows additionally `{professions_allowed: ["white_hunter","cat_burglar"], fee_multiplier: 1.5, impression_cha_delta: -2, lodging: "annex"}` (FR-CHR-001, C-9 logistics framing).

`professions.json`: 6 rows `{id, name, attr_mods:[5] per BR-3, hp_table:[20] per BR-1+extension, mp_table:[20] interpolated per Doc 1 BR-2 note, feat_rate (OQ-5), unlock_list (§5.4), start_kit:[item_ids], standing_weights}`.

`starting_tables.json` (OQ-20, verbatim from Doc 1 §10): `starting_skills` 6×9 matrix as in Doc 1's OQ-20 table (CB Marksman stored as `15` with modifier `+30` applied at creation so the FR-ADV-002 anchor is visible in data audit); `strain_skill_adds {crag_folk:{parry:5}, mesa_folk:{marksman:5}, scrub_folk:{spot_trap:5, disarm_trap:5}, lake_folk:{marksman:15}}`; `credit_by_standing {urchin:250, stoker:500, artisan:1000, patrician:2500}`; `share_by_standing {urchin:1, stoker:2, artisan:2, patrician:3}` (OQ-9); `level_award = 100 × new_level × shares` (OQ-20).

`xp_tables.json` (OQ-3): constants only — `{base:500, strain_factor{…}, profession_factor{…}, attribute_factor:{formula:"clamp(1.5-(sum-30)/100,0.6,1.5)"}}`; the engine evaluates the formula; tests verify monotone spots (WH Club-Stock, sum 60: L1→2 = 500×1×1.0×1.2 = 600).

### 5.2 R-1 — `items.json` (180 identities; ladder rows state the rule, names exhaust the ladder)

Common row: `{id, family, value, prereq:{str,dex,twostr_plus_dex}, cost, flags:["elder"], unique}` — cost ladder `[P]: cost = 25 × value × (value+1)` dollars. Prereq rules (BR-9): shields/armor `str = value`; fire `str = 4+⌈4v/5⌉, dex = same`; melee `twostr_plus_dex = 10 + value`; elder-work rows multiply all prereqs by `⌈⅔⌉` (BR-9 discount, Doc 1 §5.5).

- **shields (1–20, value = rung):** Hide Target, Wicker Shield, Rawhide Targe, Bark Shield, Hide Buckler, Copper-Rim Targe, Bronzed Hide Shield, Cane Pavise, Leather Pavise, Studded Targe, Boiler-Plate Buckler, Iron Targe, Riveted Pavise, Steel Buckler, Boiler-Plate Pavise, Chromed Targe, Club-Issue Shield, Expedition Pavise, Sun-Metal Buckler, Elder Aegis`[elder]`.
- **field armor (1–20; values 1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,10,10,11):** Canvas Jacket, Hide Jerkin, Padded Gambeson, Leather Coat, Studded Leather, Ring-Mail Vest, Scale Shirt, Chain Shirt, Bronzed Cuirass, Boiler-Plate Cuirass, Riveted Mail, Double Chain, Expedition Mail, Chrome Cuirass, Sun-Metal Scale, Club Plate, Masterwork Mail, Meteoric Mail, Sun-Metal Cuirass, **Elder Lamellar**`[elder — god-tier REQ anchor]`.
- **fire pieces (20 rungs; each = one identity with `bow_name`/`rifle_name`; outfitter subchoice (B)/(R) on buy — RS-1 one value per rung):** 1 Self Bow / Single-Shot .22 · 2 Short Bow / Rimfire Carbine · 3 Reed Bow / Farm Rifle · 4 Hunting Bow / Hunting Rifle · 5 Recurve Bow / Sporter Rifle · 6 Longbow / Bolt-Action Express · 7 Composite Bow / Express .303 · 8 Yew Longbow / Safari Express · 9 Flight Bow / Double Express · 10 Master Hunting Bow / Master Express .350 · 11 Laminated Bow / Nitro Express .400 · 12 War Bow / Big-Bore .450 · 13 Great Bow / Elephant Gun .500 · 14 Club Bow / Club Express .505 · 15 Master Longbow +1 / Master Express +1 · 16 +2 / +2 · 17 +3 / +3 · 18 Sun-Metal Bow / Sun-Metal Express · 19 Sun-Metal Greatbow / Sun-Metal Double Express · 20 **Elder Bow / Elder Express** `[elder]`. (The **Old Master-Bow** is the quest unique, mechanism = fire rung 19 bow-skin; registry entry in valuables cross-linked — §5.3.)
- **melee (40; values 1–25):** Cosh 1, Pocket Knife 1, Work Hammer 2, Machete 2, Hatchet 3, Club 3, Hunting Knife 4, Cudgel 4, Short Sword 5, Hand Axe 5, Machete +1 6, Spear 6, Cutlass 7, War Hammer 7, Hunting Knife +1 8, Cudgel +1 8, Flail 9, Broadsword 9, Hunting Spear 10, Cavalry Sabre 10, Hunting Knife +2 11, Flail +1 11, Battle Axe 12, Hunting Spear +1 12, Cavalry Sabre +1 13, Pole-axe 13, Cudgel +2 14, Flail +2 14, Hunting Spear +2 15, Cavalry Sabre +2 15, Hunting Knife +3 16, Pole-axe +1 16, Great Axe 17, Flail +3 18, Pole-axe +2 19, Cavalry Sabre +3 20, Sun-Metal Knife 21, Sun-Metal Mace 22, Sun-Metal Sabre 23, Elder Falchion 24`[elder]`, **Elder Warbrand** 25`[elder]`.

*Audit: 20+20+20+40 = 100 combat identities ✓ (180 total with §5.3).*

### 5.3 R-2 — `tonics.json`, `folio_items.json`, `valuables.json` (80 identities)

- **radium tonics 1–10:** `{id:"radium_tonic_n", hp: n², cure_tier per BR-30}` — T1–3 tier I; T4–6 tier II; T7–9 tier III; T10 tier IV `[REQ]`. Cost `[P] 50×n²`.
- **nerve tonics 1–10:** `{mp: 3n}`, cost `[P] 30×n²`.
- **folio identities (20):** `folio_I…folio_XV` (payload keys to `text/folios.json` §5.9), `folio_XVI` `{sealed:true, read_msg:"The ink has long since run to ruin."}` (OQ-12), plus 4 reading-room curios `[P]` `: club_gazette_1929…1932` (flavor: plateau society pages; zero lore).
- **valuables (40):** quest uniques — `sun_key, drowned_key, sun_gem, obsidian_urn {unique, script-linked}, crystal_resonator {bound:true per BR-35}, foul_phial, sweet_phial` (7) + `old_master_bow {mechanic: fire rung 19, unique}` (1) + 32 sellables `[P]` (name, $): smoky gem 120, fine gem 400 (FR-QST-009 yields), river pearl 60, carved idol 250, silvered compass 180, mammoth tusk 300, opal 500, star sapphire 900, topaz 350, jade scarab 275, brass astrolabe 200, scrimshaw 90, amber fist 420, silver cigarette case 150, ivory chessman 80, obsidian lens 600, ember opal 750, basalt cameo 320, fossil plaque 140, sapphire 1,200, black pearl 1,500, ruby 1,800, emerald 2,200, diamond 3,000, elder shard 5,000, tapestry fragment 450, gold pocketwatch 260, signet ring 210, platinum flask 550, moonstone 700, fire agate 640, ziggurat tile 2,600, elder lens 4,400.

### 5.4 R-4 — `feats.json` + `feat_matrix.json`

`feats.json`: 58 rows; rows 1–56 and 57–58 = Doc 1 §5.4 table rendered as `{# , name, mp, domain, class, effect:{dice?, target?, magnitude?, cure_tier?, notes}}`; #53 `{vacant:true}` (OQ-13); engine rejects learning/using vacant. All effect numbers = Doc 1 table (REQ); Vitriol rows carry `[P]` dice 1–12/1–35/1–70/1–120.

`feat_matrix.json` (OQ-5 generation; every learnable feat appears ≥1 list; `start_feat` = the profession's first list entry — the "profession starting feat" of the FRD, retained on the now-removed transfer, D-1 note only):

- **antiquarian_mesmerist** (rate 2): L1 [5,13] ← REQ anchor · L2 [1,9] · L3 [16,18] · L4 [2,19] · L5 [26,27] · L6 [10,29] · L7 [14,22] · L8 [6,17] · L9 [28,33] · L10 [20,52] · L11 [7,30] · L12 [34,46] · L13 [11,23] · L14 [41,43] · L15 [36,44,48,54]
- **expedition_doctor** (rate 2): L1 [1,22] · L2 [2,51] · L3 [23,52] · L4 [3,29] · L5 [41,24] · L6 [30,25] · L7 [42,49] · L8 [4,27] · L9 [31,44] · L10 [45,43] · L11 [26,54] · L12 [32,9] · L13 [46,10] · L14 [33,47] · L15 [11,28]
- **scout** (rate 1): L1 [52] · 2 [18] · 3 [16] · 4 [1] · 5 [19] · 6 [13] · 7 [22] · 8 [51] · 9 [20] · 10 [43] · 11 [15] · 12 [2] · 13 [17] · 14 [21] · 15 [54]
- **pugilist** (rate 1): L1 [55] · 2 [18] · 3 [22] · 4 [56] · 5 [1] · 6 [19] · 7 [23] · 8 [51] · 9 [20] · 10 [2] · 11 [46] · 12 [24] · 13 [21] · 14 [27] · 15 [54]
- **cat_burglar** (rate 1): L1 [26] · 2 [27] · 3 [43] · 4 [29] · 5 [28] · 6 [30] · 7 [37] · 8 [46] · 9 [16] · 10 [31] · 11 [47] · 12 [1] · 13 [32] · 14 [13] · 15 [54]
- **white_hunter** (rate 1): L1 [5] · 2 [18] · 3 [13] · 4 [22] · 5 [1] · 6 [16] · 7 [19] · 8 [6] · 9 [23] · 10 [15] · 11 [2] · 12 [20] · 13 [9] · 14 [21] · 15 [54]

*Audit: union = feats 1–2,4–7,9–11,13–32 (incl. 37), 41–47,49 not covered!* — check: 49 appears (doctor L7 ✓); 50 absent, 48 only AM. Fix row: AM L15 = [36,44,48,54] ✓48; add **50** to doctor L14 → [33,47,50]; add **3** to scout? present via doctor L4 ✓. 8 absent → AM L8 has 6; add 8 → AM L8 [6,8,17]? AM rate 2 allows ≤3 listed (list length ≠ slot rate; matrix lists *offerings*). Sets L8 [6,17,8]. 12 absent → AM L13 [11,23,12]. 17 already. **Result: union covers 1–52 minus 53 ✓ plus 55,56 ✓.** Final matrix = the lists above with these four amended rows.

### 5.5 R-6 — `menaces.json` (78 rows)

Row schema: `{id, name, glyph_symbol_id, tier L|M|H|VH, disp P|W|S, pack_max, hp, dmg, xp, band_min (1–5 sector distance from Terminus), flags:["M"=mummified,"C"=caster,"unique","tall"], feats?, cast_budget?, treasure: t1–t8}`. Caster rule (OQ-8): `feats` = one offense line + one control; cast-instead-of-melee 50%/round while budget > 0.

**Band 1 (low, dispositions P/W/S):** 01 marsh scuttler L W 8 6hp 1d3 12xp · 02 cave viper L S 4 8 1d4 15 · 03 leech swarm L W 6 10 1d3 18 · 04 bile slime L W 3 14 1d4 22p · 05 dune scorpion L S 5 12 1d6 25 · 06 ratling reavers L S 6 15 1d6 30 W-t2 · 07 hyena-man reavers L S 5 18 1d8 35 t2 · 08 feral ape-man L S 6 20 1d8 40 t2 · 09 drifter cutthroat L S 4 16 1d8 35 t2 · 10 drake pup L W 4 22 1d10 45 t1.
**Band 2 (low→med):** 11 ripper jackal M S 6 24 1d10 60 · 12 carrion kite M W 5 20 1d8 50 · 13 albino tunnel-folk reavers M S 5 28 2d6 80 t2 · 14 fen-man reavers M W 5 30 2d6 85 t2 · 15 sauroid hunters M S 4 34 2d8 100 t3 · 16 glider-folk swoopers M S 5 26 2d6 75 t2 · 17 wing-folk talons M S 4 30 2d8 95 t3 · 18 long-man reavers M S 4 38 2d8 110 t3 tall · 19 basalt brute M S 3 44 2d10 130 t3 · 20 bull ape M S 3 50 3d6 140 t3 tall · 21 yearling drake M W 3 46 2d10 125 t4 · 22 giant viper-moth M S 6 22 1d10+poison 90 · 23 mire lurker M S 2 42 2d10 120 · 24 banks croc M S 3 40 2d10 115 · 25 desiccated sentinel M S 8 30 1d12 85 M,t2 · 26 mummified acolyte M S 5 26 1d8 75 M · 27 renegade medium M S 3 24 — 120 C: feats[33,sleep 27] casts 2 t3 · 28 fen constrictor M S 2 48 2d12 135 · 29 bloatfly swarm M W 6 18 1d6 55 · 30 giant crayfish M W 3 36 2d8 105.
**Band 3 (high):** 31 bull drake H W 2 60 3d8 260 t5 · 32 storm brute H S 2 66 3d10 300 t5 tall (Map Room west cap set) · 33 basalt colossus H S 2 72 3d10 340 t5 tall · 34 enclave mesmerist H S 3 40 — 320 C: feats[34, dread 28] casts 3 t4 · 35 cult hierophant H S 2 44 — 350 C: feats[9, confusion 29] casts 3 t4 · 36 crag-fanatic H S 4 46 2d10 240 t3 · 37 renegade prelate H S 2 42 — 260 C: feats[33, enervation 41] casts 3 t4 · 38 hooded illusionist H S 3 38 — 290 C: feats[27, confusion 30] casts 3 t4 · 39 ether-wraith H S 3 50 2d12 330 M · 40 frost-wolf H S 5 44 2d10 230 · 41 deep one H S 4 52 2d12 310 tall,t4 · 42 pit ape H S 4 54 3d8 280 t3 tall · 43 bull saurian H W 2 62 3d8 265 t4 · 44 pen horror ripper H S 1 58 3d10 300 (lever set only) · 45 pen horror mauler H S 1 58 3d10 300 (lever set only) · 46 stonehorn H P 3 70 3d8 250 tall · 47 cliff sloth H P 2 64 2d12 220 tall · 48 plains terror-bird H S 4 48 2d12 240 · 49 sabre-tooth H S 3 50 3d8 255 t3 · 50 ridge raptor H S 4 46 2d10 235.
**Bands 4–5 (high→very high):** 51 tyrant drake VH W 1 90 4d10 1200 t7 · 52 high fiend VH S 2 80 4d8 1100 t6 · 53 deeps fiend VH S 3 75 4d8 1000 t6 · 54 blood-wraith VH S 2 70 3d12 1050 M,t6 · 55 high warden VH S 3 68 3d10 950 M?,t5 → flags M ✓ (hollow wardens) · 56 hadal cultist VH S 4 60 — 900 C: feats[34, enervation 42] casts 4 t5 · 57 hadal cult-warden VH S 2 66 3d10 980 C?: no → C: feats[35, paralysis 46] casts 4 t6 · 58 great beast VH S 1 95 4d10 1500 t6 tall (Enclave pen unique) · 59 ancient bull ape VH S 1 85 4d8 1400 unique,tall (wrestling set: no feats — §5.7 scripted) · 60 great bull ape VH S 1 88 4d8 1450 unique,tall · 61 tyrant-king saurid VH S 1 100 4d12 4000 t8 tall (D11 apex) · 62 magma newt H W 4 55 2d10 500 · 63 ember bat H S 6 30 1d10 420 · 64 soot serpent H S 4 50 2d10 470 · 65 ash crawler H S 5 42 2d8 440 · 66 obsidian crawler VH S 3 62 3d8 720 · 67 grotto crab H W 3 58 2d10 460 · 68 titan toad H W 2 66 3d8 480 tall · 69 viper swarm H S 8 26 1d8 400 · 70 glass scorpion VH S 3 56 3d8 690 · 71 fumarole wisp H W 6 24 1d8 410 · 72 sun priestess VH P 1 200 5d10 20000 unique (non-hostile; attackable — FR-QST-015) · 73 boo boo kitty VH S 1 90 4d10 5000 unique (D11 vault) · 74 lord wood VH W 1 120 5d10 30000 unique (endgame choice target) · 75 doctor voss (mortal) VH S 1 110 5d10 30000 unique · 76 doctor voss (hollowed) VH S 1 110 5d10 30000 unique, M-flag set by #57 (FR-QST-022) · 77 warden librarian M S 4 40 2d8 260 M (Map Room keeper set) · 78 mad librarian M S 5 22 1d8 130.

*Audit: rows = 78 ✓; unique bosses per BR-32 present ✓; all caster types from FR-CMB-008 present ✓ (27,34,35,37,38,56,57); mummified flag rows: 25,26,39,54,55,72?,76,77 — align: M flags on 25,26,39,54,55,76,77,78 ✓.*

**Treasure tables t1–t8** `(dollars range, item-roll chance/tier)`: t1 5–40, 10%/v1–3 · t2 20–120, 15%/v2–6 · t3 50–250, 20%/v4–9 · t4 100–500, 25%/v6–12 · t5 200–900, 30%/v8–15 · t6 400–1600, 35%/v10–18 · t7 800–4000, 40%/v12–20 · t8 1500–8000, 50%/v15–25 (+valuable roll 25%).

## 5.6 R-7 — Geography

### 5.6.1 Province (`world/province.json`, 75×50; default terrain `trail`)

Sectors: columns A–E = 15 cols each (A:0–14 … E:60–74), rows I–V = 10 rows each (I:0–9 … V:40–49). Border ring is `escarpment` (impassable cliffs — sink rule). **Terrain overlay rects** (applied in order):

```
escarpment: (8,4,20,8) (4,8,12,16) (62,2,72,6) (66,6,70,10)
swamp:      (55,40,68,48) (10,36,20,42) (44,34,52,40)
badlands:   (30,2,44,6) (12,18,18,26) (56,28,64,34)
river (polyline): (20,18)→(24,20)→(28,24)→(34,28)→(42,32)→(50,36)→(56,40)→(60,44)
crater_lake (water): (56,20,62,24)   # Drowned Ziggurat sinks here (lore; plane travel only)
```

**Feature coordinates [OD-canonical names]:**

| Feature | Pos | Sector/band | Feature | Pos | Sector/band |
|---|---|---|---|---|---|
| Terminus Post #1 | (37,24) | C-III / 1 | Xavier's Drift | (25,45) | B-V / 3 |
| Salt Landing | (8,40) | A-IV / 3 | Flagler Station | (55,8) | D-I / 4 |
| Pendry's Ferry | (20,18) | B-II / 2 | Lansing Post | (65,15) | E-II / 4 |
| Rockfell Camp | (10,12) | A-II / 3 | Scandia Port | (30,8) | C-I / 3 |
| Delta Post | (60,45) | E-V / 4 | Schatika Post | (50,30) | D-III / 2 |
| Tamarisk Mission | (52,20) | D-II / 2 | Serein Mission | (45,40) | C-IV / 2 |
| Tiernan's Landing | (70,35) | E-IV / 4 | Anvil Camp | (15,35) | A-IV / 3 |
| Deadfall Rest | (18,26) | B-III / 2 | Badlands Rest | (14,44) | A-V / 3 |
| Crown Rest | (33,14) | C-II / 2 | Campfire Rest | (28,33) | B-IV / 2 |
| Portage House | (44,20) | C-II / 1 | Royal Rest | (62,25) | E-III / 3 |
| Mirage Rest | (48,38) | C-IV / 2 | Jolly Rest | (40,10) | C-I / 2 |
| D1 The Map Room | (34,30) | C-IV / 1 | D7⇒ Drowned citadel | *plane map* | — |
| D2 Halls of the Colossi | (36,42) | C-V / 3 | D8 Wood's War-Camp | (48,6) | D-I / 4 |
| D3 Crag-Folk Burial Vaults | (8,20) | A-II / 3 | D9 Voss's Basalt Fastness | *deeps map* | — |
| D4 The Hidden Enclave | (12,32) | A-IV / 3 | D10 The Hermit's Shack | (68,8) | E-I / 4 |
| D5 The Funicular Station | (58,22) | D-III / 2 | D11 The Drake Hollows | (24,38) | B-IV / 3 |

Band rule (encounters filter, §5.8): band = 1 + max(|secCol−C|, |secRow−III|). Planar posts: Sun-Terrace Station `ziggurat_sun(9,6)`; Lake-Bottom Post `ziggurat_drowned(9,6)`; Fumarole Camp `deeps(4,7)`.

### 5.6.2 Ziggurat planes (18×9 each) & Deeps (30×15)

`ziggurat_sun`: perpetual golden-day terraces; entry/exit plaza (9,8); Sun-Terrace Station (9,6); D6 citadel gate (9,1); decorative lens pylons (2,4)(16,4). `ziggurat_drowned`: mirror layout; Lake-Bottom Post (9,6); D7 gate (9,1); gloom-water shading. `deeps`: Fumarole Camp (4,7); glyph-circle **arrival** (15,7); D9 entrance (26,7); lava course rects — crossing any lava cell = party burn (FR-QST-018; resting on non-lava safe): `(8,5,11,5) (8,10,11,10) (13,3,13,14) (16,2,18,4) (16,11,18,13) (20,6,20,8) (22,2,25,3) (22,12,25,13)`. Navigation: safe lanes exist between rects; direct routes cost 2–4 crossings.

---

## 5.7 R-8 — Site scripts (11 sites; every square a floor rect unless listed)

### 5.7.1 `site01_maproom` — "The Map Room" · pool 06,25,77,78 · entry/exit (15,22)

```
rooms: entry(13,20,17,23) stacksA(22,16,28,20) stacksB(22,10,28,14)
  pantry(22,4,27,8) waste(16,12,19,15) cupboard(16,6,19,9) office(8,14,13,18)
  westcorr((1,2)-(7,21) corridor) vault(1,1,4,3) secret(20,2,21,5)
doors: dr(14,16) lk(4,3)
panels: pn(8,16)→office[Filmon] pn(19,3)→secret
traps: dart(12,18) fume(5,5)
scripts:
 (6,19) msg "Warning — Danger lies beyond." [color registry]
 (24,6) msg — port-and-cheese table [color]      (17,13) msg — waste-paper pit [color]
 (17,7) msg — weapon cupboard [color] ; st(17,8) melee v4–6 ×2
 (10,16) menu → filmon_consult (FR-QST-020 spine; DLG set §5.9)
 (15,15) shrine menu Inspect/Destroy/Pray/Leave (FR-QST-004): first Pray → grant feat 58 (once, flag shrine.boon); later Pray → $50 × column size; Destroy → infamy(+2) + msg
 (2,2) resonator plinth: menu Take/Leave → Take: give crystal_resonator (bound, BR-35) + STR "bound"
sets: s01[06×2](5,18) s02[26,78×2](4,12) s03[77×2,27](4,7) s04[32,33](3,4)
stash: secret(21,3) t4 + diamond ; st(26,18) folio_II ; st(25,12) folio_III
```

### 5.7.2 `site02_colossi` — "The Halls of the Colossi" · pool 08,20,25,22 · entry (15,1)

```
rooms: hall(4,2,26,16) pens1–6(y18–22, x: 3|8|13|18|23|28 wide 4) leverroom(24,3,28,8)
  pit(11,6,15,10) darkchamber(1,16,5,22) cache(23,9,27,13) lockroom(9,13,11,15)
doors: dr(15,17)→pens up(10,14) msg "The lock will not yield to any pick." [FR-DGN-002]
panels: pn(15,22) escape from pen 1 [first-visit route]
traps: pitch(20,6) slab(9,9) spear(24,18)
scripts:
 (15,4) onetime chute: first entry → transport (15,20) pen 1, flag chute_fallen [FR-QST-005]
 (25,20) wall msg "KILMOR WAS HERE."
 (25,21) onetime: body of Kilmor + give folio_I, flag kilmor_found; thereafter msg "Only a bloodstain."
 pens: (5,20)(13,20) bones msg; (9,20) starved prisoner msg (freed; +$0; journal_hint)
 (26,5) lever menu 1–6,7=leave [FR-QST-006]: 3 → release [44] into room; 4 → [44] vs [45] mutual death (OQ-16: a dead beast is never a winner); others msg nothing
 (13,8) keeper challenge [FR-QST-007]: menu Accept/Refuse; Accept → mp_zero + combat [59] feats disabled; win → award_con(1,all) onetime flag wrestled
 (15,9) msg "…no devices, no draughts, no mesmerism — bare hands." [warning shown pre-entry]
 (3,19) dark chamber [FR-QST-008]: requires sun_key else eject (msg + step back); with → st(3,21) drowned_key
 (25,11) cache menu Blast/Ease [FR-QST-009]: Blast → smoky_gem×2; Ease → tr fume + fine_gem×2
 signs: (7,3) "Avoid the Colossi pens until you are strong enough." (17,3) "Find the prison block — something powerful hangs in the air there." [color]
stash: st(15,2) t5
```

### 5.7.3 `site03_craggvaults` — "The Crag-Folk Burial Vaults" · pool 25,26,36 · entry (15,1)

```
rooms: moundhall(8,4,22,10) aisles(4,12,10,18)(20,12,26,18) sarco(19,17,21,19)
traps: fume(8,12) deadfall(20,12)
scripts:
 gate: interior scripts/st msg "cold and silent" unless flag site02.kilmor_found [BR-34]
 (15,2) usher msg DLG-030 "Welcome to Kilmor's burial…"
 guest rows y5–7 examinable [canon list]: Lord Wood & Lady Katherine (9,5) · Prelate Turak (11,5) · Princess Charista & Prince Lefrod of the Lake-Folk (13,5) · High Chief Argon (17,5) · Pelzer the master bowyer (19,5) · Scrub-Folk envoys (21,5) · Kilmor's family (9,6) · his comrades (21,6)
 (15,6) column seats: onetime ceremony [FR-QST-010]: msg sequence DLG-031…035 (phantasm, thermal barrages, Voss's warning, fade) → flag funeral_done; all guest squares flip to msgs "charred bodies / empty chairs"; casket (15,4) → "ashes"
 (20,18) sarcophagus msg: unpickable, empty [FR-DGN-002]
sets: s01[36×2](4,14) s02[37,36](24,14)
stash: st(12,18) t3 funerary goods
```

### 5.7.4 `site04_enclave` — "The Hidden Enclave" · pool 13,19 · entry (15,23)

```
rooms: dining(10,4,20,9) brood(4,12,8,16) scents(24,13,27,17) records(18,13,22,16)
  temple(22,2,27,7) bench(26,5) beastpen(4,18,8,22) warrens…(corridors)
doors: dr(15,22) gate script: expedition has Crag-Folk|Mesa-Folk → open+welcome DLG-040; else DLG-041 refuse [FR-QST-011/C-9]
traps: spear(14,14) dart(22,10)
scripts:
 (15,6) feast challenge DLG-042 [FR-QST-012]
 (6,14) brood menu Snatch/Distract/Ask: Ask → msg silence; Snatch|Distract with foul_phial → give egg, chief congratulates DLG-043, give old_master_bow; without → DLG-044 "The air is bad. Come back later."; sweet_phial use → DLG-045 (attractant, wrong)
 (25,14) st foul_phial · (25,16) st sweet_phial · (20,14) records msgs · (24,4) st folio_VI
 (26,5) Old Mesmerist menu Attack/Talk [FR-QST-013]: Talk → offer DLG-046 (price: ALL carried dollars + XP tithe = 10% each member's current XP [P]) → grant feat 57 to every member with free slot AND leader (slot-free grant, Doc 1 OQ-1); revisit DLG-047; Attack → combat [19×2, 34×2]; settlement hostility never set (canon)
 (20,20) iron gate msg "immovable" [FR-DGN-002]
 (10,20) caged lake-folk huntress msg DLG-048 (warns of beast)
sets: s01[58] Great Beast (6,20) — behind: st(5,21) fire rung 18 bow-skin + t5
```

### 5.7.5 `site05_funicular` — "The Funicular Station" · pool 27,39 · entry (15,23)

```
rooms: hall(4,8,26,18) shelfrow y4–6 (x4–26) quarters(20,2,24,8) keychamber(4,2,8,6)
  leftspiral(2,10,6,16) rightspiral(24,10,28,16)
scripts:
 (10,18) wallcard DLG-050 (Mon "Time-Space Reclamation" / Tue "Matter-Energy Transference" / Wed "the Sun-Ziggurat")
 (12,18) plate: "Monday A7+ · Tuesday B7− · Wednesday C2+"
 shelves (4,4)…(26,4): dossiers Ages of Light / Chaos / Harmony / Beasts / First Age of Man / Second Age of Man / Destruction / the Present Age (msgs)
 (23,3) st folio_VII · (21,3) st folio_XII
 (6,4) cracked ceiling-lens chamber msg; st(6,3) sun_key (onetime)
 (22,4) Old Chronos Talk menu: first: senile-seneschal dialogue (DLG-051, ends asleep); later: tiers by flags (neither city / sun_seen / drowned_seen → DLG-052…054 final "I cannot do anything else for you")
 (21,6) drake: Talk/Treat/Scratch → randomized DLG-055 purrings + "Remember — Chronos takes long naps."
 (4,13) coordinate console: set letter{A,B,C}, digit{1–9}, sign{+,−}
 (26,13) Engagement Lever: C2+ → transport ziggurat_sun(9,7) flag sun_seen · C2− → ziggurat_drowned(9,7) flag drowned_seen · any other → "a far-off thrumming… nothing more"
```

### 5.7.6 `site06_sunziggurat` — gate script at (15,22): requires sun_key (unpickable) else DLG-060 · pool: none (safe zone) · entry (15,22)

```
interior mirror-maze (rooms engineered; walls per rect list)
scripts:
 arches: warm (10,10)(20,10) msg + cure tier I; scorching (12,8)(18,8)(15,6)(15,18)(7,16)(23,16) → 2d8 all, msg solar-lens ray
 statues (8,12) crag-folk elder · (15,12) lake-folk elder · (22,12) outlander: menu Leave/Break → Break: infamy(+1) each, flag statue_<id>, msg sacrilege [FR-QST-015/OQ-7]
 (15,3) Sun Priestess menu Leave/Attack/Talk: Talk (works for stained) → DLG-061: directs to Drowned citadel, names Drowned Key location (D2 dark chamber), mirror hint "remember your steps", flag met_priestess; Attack → combat [72]
 (15,5) glass table: give sun_gem (onetime)
```

### 5.7.7 `site07_drownedziggurat` — entry (15,22); mirror floor plan of site06 · pool 54,55,56

```
(15,22) gate menu Leave/Knock/Try the lock [FR-QST-016]:
  Knock → infamy 0: DLG-062 "You haven't done enough infamy to enter here." (barred) · 1–2: DLG-063 doubtful (barred) · ≥3: DLG-064 "Enter, infamous ones." (open)
  Lock → drowned_key → open + DLG-065 ("Voss is not in"); else barred [BR-34]
arches: wrong (same coords as site06 scorch set) → 80 dmg all members [REQ ~80+]
plinths (10,12) basalt vase · (15,12) pitch urn · (20,12) tar jar [ledger variants of the Obsidian Urn, canon note]: menu Leave/Take/Break → Break: show 36 scrambled words each; read rule = every 4th word across the three → decoded invitation DLG-066 + flag invitation_known; urn shards → curio (evil ending note)
 cipher: decoded 27 words fixed (DLG-066); the 81 filler words draw from a closed 24-word filler list (§5.9 STR-C1)
(15,3) black statue of Doctor Voss: if crystal_resonator not held → sets [54,55×2] then menu Take → crystal_resonator + DLG-067 "…you cannot get rid of it." [BR-35 reissue]
(15,9) glyph-circle menu (7 options, FR-QST-017): 2 place/5 throw → "It will not leave your hand." · 3 wave/6 incant → concussion, party hurled back to gate · 7 wait → nothing · 4 BREAK → transport deeps(15,7), consume crystal_resonator, flag deeps_open
(15,8) msg "Voss is not here."
```

### 5.7.8 `site08_warcamp` — "Lord Wood's War-Camp" · pool 48,50,52 · entry (15,23)

```
rooms: tent(13,2,17,5) larder(4,4,8,8) surgery(22,4,26,8) quarters(4,12,8,16) munitions(22,12,26,16) stockade(10,12,20,16)
sets (approach gauntlet to tent): s01[22×2,48×2](15,18) s02[48×3](15,14) s03[22×3,52](15,10) s04[52×2](15,7) — with approach battle-noise msgs (15,20)(15,16)
scripts:
 (15,3) Wood audience [FR-QST-019]: infamy ≥1 → msg "There is no one here." [OQ-7] · first clean visit → give folio_V + folio_XIV + plan DLG-070 · lacks feat 57 → DLG-071 "…go to the Hidden Enclave." · repeat → DLG-072 restate plan
 (24,20) quartermaster: scripted vendor (stock: fire 18–20, melee v20–25, armor rows 15–20, radium/nerve tonics 8–10, refresh per visit)
 stockade pens (12,14)(18,14): refillable fights [20] [49] (respawn on re-entry; never one-time) [optional grinding, canon]
stash: st(6,20) t8 matériel cache
```

### 5.7.9 `site09_fastness` — "Voss's Basalt Fastness" · pool 39,52,53 · entry (2,12)

```
panel route avoids every set (documented): pn seq (4,12)→(6,10)→(8,12)→(10,10)→(12,12)→(14,10)→(16,10)
set posts: s01[22×4](16,12) s02[39×2](18,10) s03[33](20,12) s04[51](22,10) s05[52×2](24,12)
msgs: (17,12)(19,12) "a lifeless chill" · (21,10) "a hideous laugh" [color]
sanctum (26,10,29,14): (27,12) Doctor Voss menu [FR-QST-021]:
 FIGHT → combat [75]
 TALK → tiers [OQ-7]: 0 → DLG-080 (+combat [75]) · 1–2 → DLG-081 · ≥3 → DLG-082
 PERFORM A FEAT → submenu (plausible-wrong list + #57) [FR-QST-022]:
   #57 unknown → DLG-083 "You do not hold that rite, fool." · wrong feat → DLG-084 "…no noticeable effect at this distance."
   #57 known → CLIMAX script: gate msgs DLG-085 (black gate; Wood steps through: "Strike now! Strike at Doctor Voss!"; Voss: "No — destroy Lord Wood, and I will raise you beside you."→"beside me.") + duel set-piece msgs (blue arc, smoke, charring [RS-8 verbatim wording]) → choice menu:
     Fight Doctor Voss → combat [76] (hollowed flag set ⇒ feat 49 effective) → good ENDING script [FR-QST-023 + OQ-18 rewards + flag ending_good; play continues]
     Fight Lord Wood → combat [74] → evil ENDING script (same structure, flag ending_evil)
```

### 5.7.10 `site10_shack` — "The Hermit's Shack" · pool: none · entry (15,23)

```
shack(13,10,17,14)
(15,12) hermit script [FR-QST-024/OQ-10]: menu Sit/Leave → Sit → broth menu (Brawn/ Wit/ Nerve/ Vigor/ Charm = STR/INT/DEX/CON/CHA): all present members +1 chosen attribute (respect caps), bowls_used +=1; prompt take second bowl now or later; when bowls_used≥1 and sitting completes → reveal msgs DLG-090 (towering shadow: "I am Doctor Voss — you have seen that my power can profit you…") + flag hermit_revealed (once-ever, BR-36); bowls_used max 2 ever
```

### 5.7.11 `site11_drakehollows` — "The Drake Hollows" · pool 10,21,31 · entry (15,1)

```
sulfur msgs along spine
rings: s01[10×4](15,6) st(15,7) t1 · s02[21×3](8,12) st(8,13) t4 · s03[31×2](22,12) st(22,13) t7 · s04[61](15,17) st(15,18) t8 + valuables
(15,21) vault: s05[73] Boo Boo Kitty msg "a pampered giant sabre-tooth" + st(15,22) diamond + elder lens
every stash square → msg "You have found a drake's trove."
```

### 5.8 `encounters_tables.json` (OQ-19)

Per-cell terrain: `trail {rate 1/12, pool: 06,07,08,09,11,48 weighted by band}`, `badlands {1/10, pool: 05,06,07,13,18,19,33}`, `swamp {1/8, pool: 01,03,14,23,24,28,29,30}`, `escarpment {1/6, pool: 19,21,31,43,46,47,50,61}`, `river {0}`; `site_interior {1/12, pool per site §5.7}`; night camp: every 10th trail move, ambush 1/3 from terrain pool, sentry Listen (FR-WLD-003). Menace selection filters by `band_min ≤ current band` (grind-mitigation §VI-7); `unique` rows never random. Surrender threshold: 50% of starting pack count dead (FR-ENC-003/OQ-19); morale: menaces flee-check at 60% losses, P(flee)=40% (Savage never → 10%).

## 5.9 Text registries

### 5.9.1 `text/folios.json` — payload map (R-5 canon numbering; topic-match per Doc 1 §11 note 3)

| # | Title | Payload topic (companion paper) | Location |
|---|---|---|---|
| I | Kilmor's Testament | Bible I (blood page) | site02 body |
| II | A History of the Cradle | II gazetteer | site01 stacksA |
| III | The Tribunal of Voices | III spiritist pamphlet | site01 stacksB |
| IV | The Crystal Resonator | IV confiscation report | Terminus outfitter |
| V | News of the Long War | XIV front dispatches | Wood audience |
| VI | The Master Bowyers | V armourer-saint folklore | site04 temple |
| VII | The Twin Cities | VI cosmogram + XII/XIII pilgrim/heretic notes | site05 shelf |
| VIII | The Map Room | VII Club minutes | Terminus outfitter |
| IX | The Halls of the Colossi | VIII survivor testimony | Salt Landing outfitter |
| X | The Crag-Folk Vaults | IX etiquette pamphlet | Pendry's Ferry outfitter |
| XI | The Mesa Enclave | X district survey | Anvil Camp outfitter |
| XII | The Funicular Station | XI antiquarian's letter | site05 quarters |
| XIII | The Sun-Ziggurat | XII pilgrim's fragment | Tiernan's Landing outfitter |
| XIV | The Basalt Fastness | XV interrogation transcript | Wood audience |
| XV | The Man Who Heard the Drowned Mind | XIII heretic's confession | Schatika Post outfitter |
| XVI | Sealed Folio | — illegible (OQ-12) | curio stock |

Full payload texts (eng: 40–90 words each; shortened here to payload + key beats, final prose authored in WP content pass per these beats — beats ARE normative): **I** Kilmor's defeat, capture, the Pens, mesmerist attempts to Hollow him, his refusal. **II** the Province, out islands (Geldern Reach, Ferrona Keys, Pogney Shoals), the northern host, Voss's landfall and conquest of the north. **III** the pattern's journey to the Séance Tribunal; recall by rite; judgement by the Bench; the Hollowed as patterns returned enthralled. **IV** the resonator: wrought by elder drowned artificers; given to Voss; corruptive bond; useless in clean hands — he would always find it. **V** the elder sun-cult's armorer-saint taught the mesa bowyers; elder masters endow true virtues; given to the proven. **VI** the five tiers: Province, Sun-Ziggurat, Drowned Ziggurat, Ember Deeps, Séance Tribunal; elder transit the only door. **VII** V as above + twin cities' mirrored splendor and exile. **VIII** Mr. Filmon's domain; mad librarians; the sealed west vaults ("so well guarded a small army would be needed"). **IX** the wrestling tribe (Colossi pens), the oubliette cells, visitors left to starve. **X** the honor of attendance at a crag-folk burial. **XI** Rockfell and the peaceable hills; the meditation warrens of the bowyer-elders. **XII** Old Chronos, older than any save the elder minds; his moving station; records in unreadable elder script; he aids worthy causes. **XIII** the Great Lens; chosen pure-hearted wardens; the Sun-Ziggurat's treasures; the Sun Priestess. **XIV** Voss's fastness in the Deeps' far tier, a "gift" of the Drowned Mind; officer-councils; the Hollowed garrison; Deeps level 3 flavor note (lore only). **XV** Voss's origin: the drowning city's pooled will *made themselves an emperor*; the gate he opened; the exodus for vengeance. **XVI** illegible.

### 5.9.2 `text/dialogue.json` — IDs (exact strings where `[REQ]`/preserved; `≈` = authored to beats)

DLG-001 filmon greeting: "I choose you because Doctor Voss would never suspect you." [REQ/D-1 single path] · DLG-002 prefix: "Listen to Mr. Filmon of Terminus Post." · DLG-010…015 the six briefs (Doc 1 §2.2 FR-QST-020 texts 1–6, verbatim) · DLG-020 "The Resonator is bound to you now. You cannot put it down." · DLG-021 shrine voice grant · DLG-030 usher: "Welcome to Kilmor's burial. You may greet the guests; the rite begins when you take your seat." · DLG-031…035 ceremony (phantasm appears; barrages; Voss: "I am Doctor Voss. What I have done today is small work. Only those who take my cause will thrive in the world I am making. I will burn out every last spark of decency on this plateau — but those who join me will be rewarded."; laughter; fade) [REQ beats, canon nouns] · DLG-040/041 warrens door welcome/refuse · DLG-042 challenge: "Take an egg from my great viper without striking her — and without being struck." · DLG-043 congratulate+reward · DLG-044 "The air is bad. Come back later." · DLG-045 attractant wrong-note · DLG-046 "For all the dollars you carry, and a measure of your memories of blood and victory, I will teach you the fifty-seventh rite — the Calling." · DLG-047 "You hold the Calling. You will know its hour." · DLG-048 huntress warning · DLG-050 wallcard · DLG-051…054 Chronos set · DLG-055 purrings (6 variants) + nap hint · DLG-060 sun-gate refuses · DLG-061 priestess: "Old Chronos said you would come… go to the Drowned Ziggurat, the mirror of this one, beneath the crater lake. Its gate answers only to great infamy — or to the Drowned Key, which lies in the Halls of the Colossi. Do the opposite of all you did here, and remember your steps." · DLG-062…065 gate voices · DLG-066 decoded invitation: "WELCOME PILGRIMS TO MY CITY. TAKE MY CAUSE AND SLAY LORD WOOD, AND GREAT SHALL BE YOUR REWARD. TO FIND ME, BREAK THE RESONATOR UPON THE GLYPH-CIRCLE IN MY SANCTUM." (27 words; cipher per §5.7.7) · DLG-067 overriding take · DLG-070 Wood plan: "…We must find Voss in the Ember Deeps and destroy him there. If I lock him in a duel of wills while you strike, we may prevail. Go to his fastness; when you stand before him, perform the fifty-seventh rite. It will open a path through which I will come." · DLG-071 Enclave pointer · DLG-072 repeat · DLG-080 "You are too pure and good for my purposes. Prepare to die, fools." · DLG-081 "You have shown some appetite for the dark. Prove yourselves truly mine — destroy Lord Wood." · DLG-082 "You have proven your nature utterly. One test remains: destroy Lord Wood, and kneel to me." · DLG-083/084 feat refusals · DLG-085 climax set (gate, "Strike now!", "No — destroy Lord Wood, and I will raise you beside me.", blue arc/smoke/charring) [RS-8] · DLG-086 good ending: Sun-Mind: "You kept faith with the Light. The Plateau remembers its friends." · DLG-087 evil ending: Drowned Mind: "You have the makings of an apostle of the Deep. Go out, and teach others your ways." · DLG-090 hermit reveal: "I am Doctor Voss. You would not like to see what it costs. Join me — and you never will." · SYS strings: "MENACE APPROACHES" [REQ], "You can't afford that", "can learn no new feats at this time", "It will not leave your hand.", "There is no one here.", "The lock will not yield to any pick.", "Unusable", plus menu titles per §5.10.3. **STR-C1** cipher filler: SHADOW, BRASS, EMBER, SALT, GLASS, WORM, LAMP, TIDE, CROWN, DUST, WIRE, MOTH, VEIL, ROOT, IRON, BELL, FOAM, GLOAM, SPAR, QUILL, ASH, REED, VAULT, HUM.

### 5.9.3 Color-text registry (Doc 1 §11 note 4 → string rows)

port-and-cheese · waste-paper pit · weapon cupboard · both Colossi signs · "The Sun-Mind is opposed by the Drowned Mind" · "Have courage, mighty travelers" · hideous laugh · lifeless chill · charred bodies/empty chairs · drake purring six-pack · "Warning — Danger lies beyond." · "KILMOR WAS HERE." · "a far-off thrumming." All pass the §5.0 lint (C-8/C-9).

---

## 5.10 Presentation registries

### 5.10.1 `text/color_tokens.json` (semantic → default RGB; restyleable, C-6)

`parchment #C8B88A · ink #2B2118 · brass #B08D57 · gunmetal #5D6466 · blood #8B0000 · gore #5A0E0E · ash #9C9C9C · stone #8A8D8F · stone_dark #555A5C · jungle #3F6B3A · fen #4E5D3A · basalt #4A4440 · trail #9A7B4F · water #2E5E7E · ember #C1440E · lava #E25822 · sun_gold #D4A017 · gloom #3A3F58 · lens_glow #F2E3B3 · hide #A08050 · ui_frame #8A8D8F · ok #7FB069 · warn #D4A017 · bad #B22222 · sleep #7A7FA8 · hollow #B0B7BB · rare #7E57C2`.

### 5.10.2 `presentation/symbols.json` — dictionary (glyph space: 0–255 CP437 literal for text/borders; entities 256+)

Members: `256 white_hunter "@" trail · 257 pugilist "@" brass · 258 exp_doctor "@" ok · 259 scout "@" jungle · 260 cat_burglar "@" ash · 261 antiquarian "@" rare` — states: `{sleeping:{fg:sleep}, down:{fg:warn}, unconscious:{fg:bad}, dead:{glyph:"%",fg:gore}, hollowed:{fg:hollow}}`. Automata: `262 mud "Ω" basalt · 263 mist "≈" ash · 264 air "π" stone`.
Terrain/features: `300 trail "." jungle · 301 badlands ":" basalt · 302 swamp "≈" fen · 303 escarpment "▲" stone_dark · 304 river "≈" water · 305 water "≈" water · 306 lava "≈" lava · 307 floor "." stone · 308 wall "█" stone_dark · 309 door "+" brass · 310 panel "█" stone_dark · 311 stairs/funicular ">" sun_gold · 312 altar/shrine "_" lens_glow · 313 plinth "_" gloom · 314 lever "/" gunmetal · 315 statue "&" lens_glow · 316 chest/cache "=" brass · 317 sign "!" parchment · 318 trap "^" bad (revealed) · 319 corpse "%" gore · 320 item_drop "]" parchment · 321 post "£" trail · 322 resthouse "≡" brass · 323 site_entrance "⌂" gunmetal · 324 glyph_circle "○" gloom`.
Menaces (78 rows; `+M` rows carry `states.mummified.fg=ash`): 325 scuttler"s"fen · 326 viper"s"jungle · 327 leech"~·"→"s"water ≈ — assign: 327 leech_swarm "s" water · 328 slime "b" fen · 329 scorpion "s" badlands · 330 ratling "r" hide · 331 hyena_man "h" hide +M · 332 ape_feral "a" hide · 333 cutthroat "c" gunmetal · 334 drake_pup "d" jungle · 335 jackal "j" · 336 kite "k" · 337 tunnel_folk "t" ash · 338 fen_man "f" fen · 339 sauroid "S" jungle · 340 glider "g" · 341 wing_folk "w" · 342 long_man "l" hide · 343 basalt_brute "B" basalt · 344 bull_ape "A" hide · 345 yearling "D" · 346 vipermoth "m" · 347 lurker "L" water · 348 croc "C" water · 349 sentinel "Z" ash +M · 350 acolyte_m "z" ash +M · 351 medium "e" rare · 352 constrictor "s" fen · 353 bloatfly "·→x" fen → "x" · 354 crayfish "c" water · 355 bull_drake "D" basalt · 356 storm_brute "B" lava · 357 colossus "G" basalt · 358 mesmerist "e" rare · 359 hierophant "E" gloom · 360 fanatic "c" basalt · 361 prelate "p" gloom · 362 illusionist "i" rare · 363 ether_wraith "W" gloom +M · 364 frostwolf "w" stone · 365 deep_one "D" water · 366 pit_ape "A" basalt · 367 bull_saurian "S" basalt · 368 ripper "R" · 369 mauler "M" · 370 stonehorn "H" basalt · 371 sloth "H" jungle · 372 terrorbird "T" trail · 393 sabretooth "c" gore · 373 raptor "r" stone · 374 tyrant_drake "D" gore · 375 high_fiend "&" gore · 376 deeps_fiend "&" lava · 377 blood_wraith "W" blood +M · 378 high_warden "W" ash +M · 379 hadal_cultist "h" water · 380 cult_warden "H" water · 381 great_beast "B" gore · 382 ancient_ape "A" gore · 383 great_ape "A" gore · 384 tyrant_king "K" gore · 385 magma_newt "n" lava · 386 ember_bat "b" lava · 387 soot_serpent "s" lava · 388 ash_crawler "x" ash · 389 obsidian_crawler "x" gloom · 390 grotto_crab "c" gloom · 391 titan_toad "T" fen · 392 viper_swarm "s" bad · 394 glass_scorpion "s" lens_glow · 395 wisp "·"→"o" ember · 396 sun_priestess "P" sun_gold · 397 boo_boo_kitty "c" sun_gold · 398 lord_wood "L" trail · 399 voss "V" gunmetal · 400 voss_hollowed "V" hollow +M · 401 warden_librarian "l" ash +M · 402 mad_librarian "l" gore +M.
*(IDs unique 325–402 ✓ = 78 entries; each maps to §5.5 row order.)*

### 5.10.3 `presentation/menus.json` — static descriptors (scripted-square menus come from R-8, §5.7)

Format `{id, title, region:"bottom_center", options:[{key,label,verb,args}]}`. Descriptors: `boot`[1 Start at Terminus→session.new · 2 Continue→menu save_slots · 3 Demonstration→session.demo · 4 Utilities→menu utilities] · `utilities`[1 Backup member→util.backup · 2 Restore member→util.restore · 3 New game (ERASES)→util.new_game_erase confirm submenu] · `post`[1 Explorers' Club chapter→menu chapter · 2 Letter-of-credit→menu credit · 3 Outfitter→menu outfitter · 4 Debrief officer→post.debrief · 5 Infirmary→post.infirmary · 6 Perform a feat→post.use_feat · 7 Use an item→post.use_item · 8 Distribute & sell→post.distribute · 9 Trade→post.trade · I Inspect member→post.inspect · S Save game→menu save_slots · L Leave Post→post.leave] · `chapter`[N New member · L List · A Add to expedition · D Drop · R Rename · P Purge · T Training · F Learn feats · Q Leave] (+ designate-automaton implicit via Add, FR-CHR-008) · recruit flow: `strain`[1–5 charter, 6 Strange] → `profession`[1–6; strange→1 White Hunter, 5 Cat Burglar only] → `accept`[A accept / R reject] · `credit`[W Withdraw / D Deposit] · `outfitter`[L list · C continue · # buy · T trade-sell · Q] · `trail`[P Perform · I Inspect · U Use tonic · R Rest/camp · G Time-lag & sound → menu config] · `encounter`[1 Fight · 2 Accept Menace's Surrender · 3 Parley · 4 Beg for Mercy · 5 Flee] · `tactic`[1 Thrust · 2 Attack · 3 Slash · 4 Lunge · 5 Aim · 6 Feat · 7 Parry · 8 Fire · 9 Other→menu tactic_other] · `tactic_other`[R Rank (F/M/B) · T Time lag · S Sound · D Redo] · `site`[L Look · menu-driven contextual options emitted by scripts] · `config`[T 0–9 · S on/off] · `save_slots`[1–4 + 0 show autosave note]. Every option resolves to a §6.1 verb — **lint rule**: no descriptor may name a verb not in the registry.

### 5.10.4 `presentation/demo_script.json` (ADR-6; fixed seed 7)

`session.new` → accept starter six (FR-CHR-002) → `shop.buy` folio_II → `post.use_item` read → `post.leave` (autosave) → trail walk S×6 → seeded encounter [06] → 3 rounds (thrust/attack/fire scripted) → victory → `trail.move` N×6 → post → `session.save` slot1 → `session.quit_to_menu`. Runs unattended through the normal display path; any DomainError aborts demo silently to menu.


## 6. API Specification

(§5 Data Layer follows as installment II; placed before §6 in final assembly. §6 defines the runtime contracts all later sections and all tests consume.)

### 6.1 Command interface — `engine.commands`

Single entry point: `Engine.dispatch(cmd: Command) -> list[Event]`. `Command = { verb: str, actor: int | None (column index 1–6), args: dict }`. Verb registry (closed enumeration; menus only emit these — C-6):

- **session:** `session.new`, `session.continue{slot}`, `session.demo`, `session.save{slot}`, `session.quit_to_menu`
- **utilities:** `util.backup{member}`, `util.restore{filename}`, `util.new_game_erase{confirm: bool}` (FR-SAV-003; D-1: no transfer verb exists)
- **chapter:** `chr.begin_recruit{}`, `chr.pick_strain{strain|"STRANGE"}`, `chr.pick_profession{prof}`, `chr.accept{name}|chr.reject{}`, `chr.list{}`, `chr.purge{member}`, `chr.add{member}`, `chr.drop{member}`, `chr.rename{member,name}`, `chr.designate_auto{mud|mist|air}` (FR-CHR-008)
- **advancement:** `adv.train{member}`, `adv.train_skill{member, skill}` ×3 within one training session, `adv.learn_feat{member, feat_id}`
- **post:** `credit.withdraw{member, amount}`, `credit.deposit{amount}`, `shop.list{page}`, `shop.buy{item_no}`, `shop.sell{item}`, `post.debrief{}`, `post.infirmary{}`, `post.use_feat{member, feat, target?}`, `post.use_item{member, item}`, `post.distribute{}` (opens pool), `post.trade{src_member, dst_member, item}`, `post.inspect{member}`, `post.leave{}` (⇒ autosave: FR-TWN-005)
- **trail:** `trail.move{dir:N|S|E|W}`, `trail.perform{member, feat, target?}`, `trail.use_tonic{member, tonic, target_member}`, `trail.inspect{}`, `trail.camp_rest{}`
- **site:** `site.move{dir}`, `site.look{}`, `site.listen_continue{proceed: bool}`, `site.pick_lock{member}`, `site.spot_trap{}`, `site.disarm{member}` / `site.leave_trap{}`, `site.choose{option_index}` (scripted-square menus), `site.exit{save_state: bool}`
- **encounter:** `enc.fight|enc.accept_surrender|enc.parley|enc.beg_mercy|enc.flee`
- **combat (per member per round):** `cmb.thrust{cmb.attack|cmb.slash|cmb.lunge{cmb.aim target}` with `{target_rank}`, `cmb.feat{feat_id, target_rank?|target_member?}`, `cmb.parry{}`, `cmb.fire{target_rank}`, `cmb.rank{front|middle|back}`, `cmb.redo{}` (column reset, FR-CMB-001), `cmb.config{time_lag, sound}`
- **meta:** `menu.choose{option_key}` is the uniform envelope for all numbered/lettered/Y-N prompts listed in FR-UIX-002; `menu.return{}` = RETURN-continue.

Every `dispatch` returns an ordered `list[Event]`; rejected verbs return `[DomainErrorEvent]` and mutate nothing (§11).

### 6.2 Events — `engine.events`

`Event = { kind: str, tick: int (engine clock), data: dict }`. Closed kind set: `MSG` (player text), `MENU` (open menu descriptor id + context), `STATE` (state delta: member/party/world field changes), `MAP` (map reveal/position), `COMBAT` (round results incl. swings/body hits/status letters K/S/U/D), `SFX_FLAG` (emitted, inert — D-2), `SAVE_WRITTEN`, `ENDING`, `ERROR`. The composer consumes only these events + the state projection; never calls engine mutators (C-6).

### 6.3 Frame contract — `ui.frame`

```python
Layer = { symbol_id: int, fg: str, bg: str, flags: set[str] }   # token names only (C-6)
Cell  = { layers: list[Layer] }                                 # terrain < item < actor < fx < ui
Frame = { w: 120, h: 40, cells: list[list[Cell]], tick: int }
```

Symbol ids 0–255 = literal CP437 for UI text/borders; ≥256 = entities through `symbols.json` entry: `{glyph: int|str, fg: token, bg: token, states: {state_name: {glyph?, fg?, bg?}}}` (Doc 1 §6.2 exemplar). Renderer protocol (text now, tile later): `render(cells: Frame) -> None`, `poll() -> KeyEvent` — `render/tile_iface.py` declares exactly this interface (swap contract, ADR-1).

### 6.4 Save/backup documents

`SaveDoc = { schema_version: 1, rng_state, tick, clock_days, roster: [MemberDTO ≤ 30], expedition: ExpeditionDTO, world: WorldDTO{ site_states: {site_id: {grid_delta, flags}}, one_time_flags, infamy, milestone, quest_score }, treasury, config_echo }` (OD-6; Doc 1 §6.3). Member backup export: `{schema_version, member: MemberDTO}` (FR-SAV-003). All loads range-checked + schema-validated before any state touch (§7/§11).

### 6.5 Site script DSL (runtime vocabulary of R-8, Doc 1 §6.4)

`ScriptSquare = { at: [x,y], on: "enter"|"menu"|"flag_set", if: {...gates}, then: [Action...] }`; closed Action verbs: `msg, menu(id, opts), combat(set_id), give_item(id), take_item(id), set_flag(f), damage(area_spec, dice), mp_zero, transport(map_id,x,y), award_con(amount), award_xp(n), journal_hint(string_id), infamy(n), ending(kind)`.

## 7. AuthN/AuthZ

None exists and none is added (C-7; single-player local). Two authorization-shaped concerns land elsewhere: **game-rule gates** (BR-34/infamy/Enclave strain gate) are engine logic in `quests.py`/`sites.py`, not security; **file trust boundaries** are handled by §6.4 validation — a malformed save is hostile input and is rejected without state mutation. No credentials, no secrets, no PII.

## 9. Background Jobs

None. Turn-based dispatch only; no threads, no timers, no async I/O anywhere (protects determinism, C-3). The three "ambient" behaviors are synchronous: autosave executes inline inside `post.leave` handling (FR-TWN-005); night-camp checks execute inline inside `trail.move` every 10th step (OQ-19); the attract reel is `app.py` idling at the boot menu for 60 s [ADR-6] then dispatching `session.demo`. `clock.py` implements time-lag (0–9 × 150 ms message hold) as render-loop pacing only; it cannot touch state.

## 10. Observability

(1) **Event stream** is the primary telemetry (§6.2) — `simcli.py` can dump it. (2) **RNG draw log:** every `SeededRng` draw records `{tick, caller, distribution, result}`; replay hash = SHA-256 over concatenated results; `simcli --hash` prints it for golden comparison (C-3; §12). (3) **Debug log:** human-readable lines to `logs/debug.log` when debug enabled (§4); silent by default. (4) No telemetry/crash-reporting network paths exist (C-7). (5) Renderer frame-rate logging is dev-only and never in release builds.

## 11. Error Handling

`errors.py` taxonomy: `DomainError` (rule rejection: can't afford, gate locked, wrong domain — surfaced as `ERROR`/`MSG` event, state untouched, play continues) · `ContentError` (registry/script/schema violation — raised at boot load, names file+row, process exits non-zero; never at runtime) · `SaveError` (schema version mismatch, range violation, corrupt JSON — user-facing load failure, returns to menu, no partial state) · `InvariantBreach` (dev-build assert in `state.py`: BR-8 caps, BR-36 flags, treasury/credit ceilings — crash in tests, compiled out in release via flag). Unexpected exceptions: `app.py` top-level guard logs traceback (debug on) and exits; recovery = `session.continue` on autosave slot (Doc 1 §9). Command handlers never raise to the loop for domain rejection; validation happens before mutation (check-then-act in one method per verb).

## 12. Testing Strategy

Stack: `pytest` driving the engine **headlessly** (C-3), plus composer snapshot tests; renderer is excluded from logic tests (thin blit only; smoke-tested in §13).

**Rules of construction (binding):** (a) tests reach state only through `Engine.dispatch` and `content` registries — **no fixture may hand-build game state the production path is supposed to produce**: pre-existing state is established by issuing command sequences (shared `tests/harness.py` helper `run_script(verbs)` that itself only dispatches production commands); a test that pre-builds its inputs is a defect to be rejected at review. (b) Determinism: every test runs with explicit seed; golden tests compare event-stream hash. (c) Content tests validate registries against Doc 1 anchors (e.g., BR-1 rows, feat #5 = 1–10, #53 vacant, 180/78/56 counts, FR-UIX layout regions in menus.json).

Layers: **unit** (per §8 module pure functions; skills checks, BR-30 healing tiers, formula tables OQ-3/4/20) · **verb tests** (each §6.1 verb: happy path + every documented alt flow from Doc 1 §2.2) · **integration** (encounter→combat→spoils; site entry→scripts→exit/save-state; tribunal; infamy gates; ending branches ×2) · **golden campaigns** (`tests/golden/`: scripted command files — `golden_good`, `golden_evil`, `golden_tribunal`, `golden_site_reset`, each incl. assertion on final state + replay hash) · **properties** (generation-based: ceilings never exceeded, XP divide conserves total, one-time flags monotonic). Coverage floor: every verb, every feat effect, every FR-QST milestone, every BR table edge row has ≥1 test; engine line coverage ≥ 90%.

## 13. Build/Run/Deploy

Dev: `pip install -e .[dev]` → `cradle` (windowed, C-1/C-2) or `python -m cradle.simcli script.txt --seed N --hash` (headless). Content check: `cradle-content-check` (loads all registries, runs anchor validation — same code path tests use). Deploy: `pyinstaller deploy/pyinstaller.spec` → one-folder bundle per OS (A-4); assets (fonts, `content/`) bundled via spec `datas`; version string from `pyproject` into `platform/config.py` echo. Smoke procedure post-package: boot → demo reel auto-plays → new game → save/continue round-trip.

## 14. Acceptance Criteria

A build is accepted when **all** hold (mirrors Doc 1 §2; each cites its anchor):

- **AC-FR (95/95 as amended):** every FR entry in Doc 1 §2.2 has ≥1 passing test keyed by FR-ID; D-1 removals (transfer verb, veteran greeting) verified *absent*; D-2 toggle verified functional-silent.
- **AC-CMB:** golden melee script verifies tactics fallbacks (FR-CMB-002), rank relativity with uniform ranks ⇒ zero modifier (FR-CMB-003), CB any-rank / WH lunge rank-2 reach (FR-CMB-004), auto-hit Sleeping (FR-CMB-005), ballistics tables (§5 R-6b), found-item cap 90 + unusable-until-distributed (FR-CMB-007).
- **AC-Economy:** BR-7 ceilings reject overflow; deposit exemplar $6,000/6 ⇒ $999; BR-10 tonic formulae; OQ-4 cost curve spot values ($3,520 mid case; $17,550 tail) reproduce.
- **AC-QST:** the 25 milestones execute in BR-34 gate order; funeral gating on Kilmor; Enclave strain gate; key/inflamy Drowned-gate matrix (pure/stained barred, blackened welcomed, key bypass); Wood absent at infamy ≥1; #57-only ether-gate; Voss Hollowed flag → #49 effective; both endings + continue-play.
- **AC-Persist:** post-only saves; autosave on every `post.leave`; mid-field quit resumes at last post; site save/original choice; one-time items never restored; backup/restore round-trips.
- **AC-Determinism:** `golden_good` and `golden_evil` replay hashes stable across 3 runs on 2 OSes; same script+seed ⇒ identical hash (C-3).
- **AC-Presentation:** boot at 120×40; six-region layout present (FR-UIX-001) via composer snapshot; every glyph resolves via dictionary (no raw chars in code — lint rule); time-lag 0 vs 9 measurably changes pacing; demo reel plays without input.
- **AC-Campaign:** headless completion of both endings from fresh seed (GOLDEN scripts) with zero hand-built state (§12 rule a).
- **Traces:** all `TRACE-01…12` in §15 execute as scripted tests.
