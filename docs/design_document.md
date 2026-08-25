# DESIGN DOCUMENT

**Title:** *The Cradle Plateau: The Wrath of Doctor Voss* — System Design
**Version:** 1.0.0 · **Date:** 2025-06-13 · **Status:** Draft
**Governing inputs:** Operator decisions OD-1…OD-8 (interview, confirmed); requirement authority transferred in full from the sealed source FRD set under mandate SC-1.

## Revision History

| Version | Date | Status | Changes |
|---|---|---|---|
| 1.0.0 | 2025-06-13 | Draft | Initial delivery. |

## 0. Reading Map & Authority

This design document and its successor technical specification are the **sole authority** for implementation (SC-1; OD-8). No external source document exists for the implementer. Four content classes appear, each traceable:

| Tag | Meaning |
|---|---|
| `[REQ]` | Requirement transferred verbatim in value from the sealed requirement register (FR/BR/R/§VI IDs). |
| `[OD]` | Operator decision OD-1…OD-8 (interview record). |
| `[P]` | `[PROPOSED DESIGN DECISION]` — a value invented under OD-4 authority where the sealed register quarantined it. Reviewable line-by-line. |
| `[D]` | Deviation from the sealed register, operator-directed: **D-1** veteran transfer removed; **D-2** sound toggle ships functional with no audio output. |

**Feat of note on naming [OD-1].** All proper nouns use the canonical layer (Doctor Voss, Terminus Post, Mr. Filmon, Kilmor…). The sealed narrative companion survives as dialogue/flavor author-of-record, re-authored onto canonical nouns under its own binding rule: menu option counts/order, gating, rewards, and persistence flags are never altered by re-authoring.

**Document division of labor (SC-1 across the set).** Doc 1 carries: every requirement, every verbatim table, every rule/formula, all OQ resolutions, complete schemas and anchors. Doc 2 §5 carries: exhaustive row-level data (all 180 items, 78 menaces, 56 feats derived from §10 rules, sector map, site grids, full dialogue/folio text). No value may appear in Doc 2 that is not either `[REQ]`, `[OD]`, `[P]` in Doc 1, or mechanically implied by one — enforced by Doc 2 §16.

---

## 1. Overview & Goals

**Product.** A single-player, round-based, expedition CRPG in 1930s-pulp lost-world dress. The player recruits and commands a column of up to six Club members (5 charter strains + 10 strange strains, 6 professions), leads them across a fixed authored province and five terrain sets, rounds of positional tactical combat with six woundable body locations per combatant, a hidden infamy track, and a fixed 25-milestone quest ending in a moral choice — fight Doctor Voss, or fight Lord Wood — with two distinct endings. `[REQ: product overview]`

**Presentation.** Every screen is a grid of colored characters (CP437, roguelike-style) behind a three-layer architecture that allows a later tile-and-menu presentation swap **without touching game logic** [OD-2; operator presentation brief, accepted as binding].

**Goals.**
1. Byte-faithful mechanics: 95 feature requirements, verbatim business-rule tables, fixed quest spine and gates.
2. Full self-containment (SC-1): this document set alone is sufficient to build and accept the game.
3. Determinism [OD-5]: one seeded PRNG; headless completability; golden replays.
4. Presentation swap-readiness: logic never reads the display grid; all content data-driven.

**Explicit non-goals** `[REQ: §I boundary; OD-3; OD-7; OD-6]`: multiplayer/networked play; real-time/reflex play; procedural generation; post-victory world acknowledgement; modding/user editors; pointer input v1; audio output v1 (D-2 — toggle ships, functional, silent); a built tile renderer (designed-for, not built); veteran-saga transfer (D-1); media-era cheats/copy protection; save-migration code pre-1.0; any third-party service, telemetry, or account.

---

## 2. Requirements Summary

### 2.1 Constraint Register (governs §§3–10 of this document and all of Doc 2)

| ID | Constraint | Source |
|---|---|---|
| C-1 | Python 3.12 + python-tcod; SDL-backed window; fixed 120×40 virtual console (8×16 cells → 960×640, integer scaling) | OD-2 |
| C-2 | Keyboard-only input v1 | OD-2/OD-7 |
| C-3 | Single seeded PRNG at the composition root drives **all** randomness; seed state persisted in saves; full game headlessly completable | OD-5 |
| C-4 | Saves: single local JSON per slot, human-readable, schema-versioned; breaking changes allowed pre-1.0 | OD-6 |
| C-5 | Sound toggle functional, zero audio output v1 | OD-7 (D-2) |
| C-6 | Simulation never reads the display grid; all glyphs via symbol dictionary (IDs 0–255 CP437 text, 256+ entities); semantic color tokens; menus as data | Operator brief |
| C-7 | Single-player, single-process desktop; no network, telemetry, accounts, third-party services | [REQ §I, §VII-5] |
| C-8 | Magic ban: every feat is fictionally a device, drug, or documented psychic feat; no sorcery, gods, or non-pulp supernaturalism in any string | [REQ §I, T2 constraint] |
| C-9 | Modern-care clause: strains are sapient peoples; stat deltas are physiology, never "civilization"; standing rolled independently; strange-strain drawbacks framed as logistics/first impressions; no period rhetoric in any text; fauna are fauna; the villain is a European occult-scientist | [REQ §I guardrails; RS-2] |
| C-10 | Session topology: every session begins and ends in a post; manual save post-only; autosave on every post exit; resume always at a post | [REQ §VI-1/2; FR-SAV-001] |

### 2.2 Functional Requirements (all 95, telegraphic restatement; IDs canonical)

**FR-SES — Session (4).** · 001 Start new game → Post Menu of Post #1 (Terminus), empty expedition; muster at chapter; no failure path. · 002 Continue → resume at saved post, expedition intact (roster-number restore prompt is packaging; single canonical model, FR-SAV-004). · 003 Demo: automated lantern-lecture attract reel; no failure path. [A-1: implemented as scripted playback through the display model.] · 004 Utilities: prepare play media; **backup/restore members**; new game with explicit erase-confirmation (decline aborts). **[D-1: the transfer-veterans branch is removed.]**

**FR-CHR — Creation & roster (8).** · 001 Recruit: pick charter strain (Club Stock, Crag-Folk, Lake-Folk, Mesa-Folk, Scrub-Folk) or "Strange Strain" (system picks one of ten: Hyena-Man, Albino Tunnel-Folk, Ratling, Sauroid, Ape-Man, Basalt Brute, Fen-Man, Glider-Folk, Wing-Folk, Long-Man); one of six professions — White Hunter, Pugilist, Expedition Doctor, Scout, Cat Burglar, Antiquarian-Mesmerist (strange strains: White Hunter or Cat Burglar only). System rolls attributes (base random + profession modifier, capped at strain maximum), standing (charter strains trend higher), starting age, Luck 8–13, starting credit line, starting kit. Accept (name, full sheet, roster add) or reject. Strange-strain drawbacks: low first-impression Charisma tendency, higher outfitting/tuition fees, annex lodging [C-9 framing]. · 002 Pre-generated expedition: six pre-equipped level-1 members (hunter, doctor, antiquarian-mesmerist, scout, cat burglar, pugilist) occupy slots 1–6 [OQ-15 ⇒ P-decision: shipped on all builds]. · 003 List members: name, profession, resident post; final three slots = automata Mud, Mist, Air resident "post 0" (the hangar). · 004 Purge member: permanent, "use with caution", no undo. · 005 Add to expedition: <6 members, member resident in this post. · 006 Drop: member returns to roster in current post. · 007 Rename: no failure path. · 008 Designate automaton: adding Mud/Mist/Air marks which one Hangar Dispatch calls; consumes no expedition slot.

**FR-ADV — Advancement (5).** · 001 Level training: sufficient XP + treasury dollars → Level +1: max HP per BR-1; skill training in **exactly three skills** (same skill repeatable, diminishing per BR-5); dollar award scaled by standing. Errors: report XP still needed; report insufficient funds. Cost formula OQ-4 ⇒ §10. · 002 Nine percentage skills: Attack, Parry, Swim, Listen, Spot Trap, Disarm Trap, Find Item, Pick Lock, Marksman; situational modifiers may exceed 100 or reduce below 0. Anchors: Cat Burglar +30 Marksman; Lake-Folk +15 Marksman. · 003 Feat learning: unlock list by profession/level/INT; per-attempt cost from treasury; consumes one learnable slot; "can learn no new feats at this time" branch. · 004 MP growth: infirmary/rest-house stay after MP spent → chance to raise *maximum* MP, bounded by BR-2 ceiling. · 005 XP accounting: battle XP accrues; divided among members on return to a post; dollars to treasury immediately after each battle.

**FR-TWN — Post services (7).** · 001 Letter-of-credit counter: Withdraw (member credit line → treasury) / Deposit (treasury divided into 1/2/3 shares per member [basis OQ-9 ⇒ §10], less deposit fee, rounded down). Ceilings: credit line ≤ $65,000 each; treasury ≤ $65,000 [canonical constrained model chosen, §10 ADR-5; pooled $10⁹ presentation preserved as packaging note only]. No-op branches; overflow rejected. · 002 Outfitter: one shopper designated; stock listed a dozen at a time (List/Continue) showing number, name, cost, point value; unsupported items flagged **Unusable**; buy → shopper kit (≤9), debit treasury; selling via Trade ("berth 7") or Distribute; folios/curios persist once stocked, weapons/tonics restock and vary; "You can't afford that"; kit-full branch. · 003 Debrief officer: reports score 0–100 + rating (preserved exemplar: score 43 → "average"); no failure path. · 004 Infirmary: free full rest — all HP/MP to max; cures 1 Broken **or** 2 Injured areas per stay; triggers FR-ADV-004. · 005 Leave post: **auto-save**, then enter wilds adjacent. · 006 Post utility actions: perform post-legal feat (e.g., #54 Supply-Line Recall, cross-planar); use item (read folios — **post-only** [RS-5], quaff tonics, probe items); Distribute & sell (pool, per-item usability per member, listed best→worst elder-work first); Trade member-to-member; Inspect member (full sheet incl. surgeon's body diagram); non-post feats not offered. · 007 Save game: persist.

**FR-WLD — Trail (6).** · 001 Movement N/S/E/W; province pre-surveyed ⇒ fully visible; 25-sector labeling (columns A–E, rows I–V). · 002 Terrain: game trails (easiest, widest menace variety); basalt badlands (easy; raiding-strain menaces); swamps (harder; insect/slime); escarpments (very hard; megafauna); croc rivers (each member rolls Swim; failure = potentially lethal drowning damage; no encounters in water). · 003 Random menaces per terrain tables [rates OQ-19 ⇒ §10]; night ambush while camped: sentry Listen roll rouses camp, else members start Sleeping (feat #51 accelerates waking). · 004 Rest-houses: rest as FR-TWN-004 for $250 "plus tax"; can't-afford branch. · 005 Site approach: identify, confirm enter; data-swap prompts abstracted away. · 006 Trail utilities: Perform (Field/Everywhere feats), Inspect (time out, XP, dollars, items this leg, per-member summary), Use tonic (self/other), time-lag/sound configuration.

**FR-DGN — Sites (6).** · 001 Auto-map: blank until explored; **Look** reveals several squares, not through walls (large chambers may exceed one Look); Look-always mode rejected as packaging. · 002 Doors/locks: doors bar movement/sight; auto-Listen at doors (success → warning + turn-back option); Pick Lock; unpickable/scripted-only locks preserved (Halls of the Colossi unbreakable lock; Hidden Enclave immovable iron gate; Burial Vaults unpickable empty sarcophagus). · 003 Hidden panels: move through apparently solid wall concealing passage; no other signal. · 004 Traps: Spot Trap detection → Disarm (exactly one member; failure triggers) or Leave. Effects: dart fusillade (fire arrows), boiling-pitch sluice (molten lead), counterweight slab, spear-snare, fume vent (poison gas), deadfall (rocks). · 005 Scripted squares: description text, dialogue menus, set-piece combat, item acquisition, transport (registry per FR-QST + R-8). · 006 Exit & persistence: offer leave; offer **save site state**; re-entry: menaces may reset traps/locks and re-man; quick return may retain dead menaces; **one-time events/items never respawn**, even on restore-original (BR-36).

**FR-ENC — Encounters (8).** · 001 Sequence: "MENACE APPROACHES" → identity, ranks, statuses → menu **Fight / Accept Menace's Surrender / Parley / Beg for Mercy / Flee**, re-shown after every combat round. · 002 Fight → melee. · 003 Accept surrender: after menace losses ≥ threshold [OQ-19 ⇒ §10 P: 50%]: receive all items and dollars; too-early refusal branch. · 004 Parley: may avoid combat with non-hostiles; no response → battle; free on failure. · 005 Beg for mercy: on acceptance menaces take **all expedition dollars + some new items**; refusal branch. · 006 Flee: success avoids; failure → menaces get free attacks. · 007 Menace morale: reorganize each round; may flee when losing; combat ends on death/surrender/mercy/flight. · 008 Dispositions Placid/Wary/Savage per type (R-6).

**FR-CMB — Melee (8).** · 001 Tactics per member per round: **Thrust** (1 swing, best accuracy, +1–2 dmg), **Attack** (2 swings), **Slash** (3–4 swings, less accurate, −1–2 dmg), **Lunge** (White Hunter only; 1 normal swing at a second-rank menace), **Aim** (1 swing head/torso, reduced accuracy), **Feat** (any Combat/Everywhere feat + target), **Parry** (shield raise, displayed), **Fire** (bow/rifle, pick rank), **Other** (move Front/Middle/Back; time lag/sound; **Redo** resets whole column before execution, available after all assigned). · 002 Fallbacks: insufficient Attack % → Thrust; Slash → Attack; Aim → Thrust; non-hunter Lunge → Thrust. · 003 Positions: Front (+to hit/+to be hit), Back (inverse, weaker), Middle neutral; **modifiers relative to the rest of the column** — uniform ranks = no modifier; position never affects Fire. · 004 Reach: Cat Burglars Thrust/Attack/Slash any rank; White Hunters Lunge rank 2; bows/rifles/feats any rank. · 005 Status: Sleeping auto-hit; Down much easier to hit but can dodge; rank-line statuses K/S/U/D. · 006 Body-area ballistics: bows/rifles best head/torso chance; feats equal everywhere; hand weapons worst, worse vs very tall menaces; Aim partially offsets; feats 5–8 and 37–40 strike a specific body area; 33–36 HP only. [RS-1: rifles inherit bow ballistics; no ammo economy — Fire stays unlimited.] · 007 Resolution: turn order; results window + expedition panel; victory → XP total + dollars displayed (dollars→treasury; XP per FR-ADV-005); trail/surrender treasure automatic; **in sites, Find Item rolls**; found-items cap 90, unusable until distributed at a post. · 008 Feat-using menaces: caster types (Renegade Medium, Hooded Illusionist, Enclave Mesmerist, Cult Hierophant, mummified acolytes…) use feats vs the column [repertoires OQ-8 ⇒ §10]; enemy mesmerists can counter column feats (INFERRED note preserved).

**FR-BOD — Body/mortality/aging (6).** · 001 Six locations (head, torso, L/R arm, L/R leg), states Okay/Injured/Broken/Gone; surgeon's stick-figure diagram; death at 0 HP **or** head/torso Gone. · 002 Consequences: any arm/leg Broken → cannot Fire; right arm Broken/Gone → no swings, no feats; **Parry is the only combat option**. · 003 Healing: infirmary stay; Suture 1–4 (1–9/1–27/1–57/1–99 HP) and radium tonics cure per BR-30, most vital area first (Gone = break+injury; Broken = 2 injuries). · 004 Revivification (#44): dead target; revival chance; **CON −1..2 permanent**. · 005 Séance Tribunal on total expedition death: per-member judgement — **Returned** (revives; loses carried dollars; −1 CON) or **sent back Hollowed** (level set 20, frozen from training/improvement) [probabilities OQ-11 ⇒ §10]. Lore basis: Folio III. · 006 Aging: time passes with travel/rest; members age; past strain-specific declining years, attributes deteriorate [schedule OQ-6 ⇒ §10]. Lifespans: Lake-Folk ≈3000 yr; Crag-Folk/Mesa-Folk ≈200; Club Stock ≈80; strange strains 40–50 [RS-3 longevity handwave preserved].

**FR-MAG — Feat economy (5).** · 001 Feat engine: MP cost 1–4; domains Everywhere/Post/Field/Site/Combat; classes **Passive** (non-cumulative; counters opposing active effect — Adrenal Surge cancels enemy Slow) / **Active** (cumulative; exceptions: Dread stacks, Sleep doesn't deepen, Paralysis/Confusion/Enervation progressive). MP is one pool — no ammunition/charge/dose inventories [RS-1]. · 002 Complete registry: 56 feats, #53 vacant, elder rites 57+; effect figures per registry R-4 (§5.4): Suture dice, Thermal Lancet 1–10/1–30/1–60/1–100 one area, Thermal Sweep 1–7/1–15/1–31/1–66 every menace armor-mitigated, Mesmeric Assault 1–5/1–11/1–41/1–81 HP-only, Adrenal Surge +10/25/45/70%, Nerve-Hardening +1/3/6/10 armor, Incendiary Loads (+50% acc, +15 Fire value)/Party/Express (+100%, +25), Trance → Marksman 250, Charm (friendly until attacked), Sleep, Confusion (impedes enemy feats), Enervation (reduces damage), Paralysis (inhibits movement, easier to hit), #43 Egress, #44 Revivification, Pugilist's Trance 1/2 (**Trance 2 stronger at lower MP — quirk preserved**), Dread, Vitriol Projector, #48 Hangar Dispatch, #49 Counter-Talisman Rites (mummified flee or crumble), #51 Awaken, #52 Field Assessment (approximate; occasionally wrong), #54 Supply-Line Recall. · 003 Elder rite **#57 The Calling**: acquired only from the Old Mesmerist (FR-QST-013); in Voss's presence opens the black ether-gate pulling Lord Wood through (FR-QST-022). · 004 Shrine rite: Sun-Mind's Boon, granted once at the Map Room shrine (FR-QST-004); number/effect OQ-1 ⇒ §10. · 005 MP economy: spend per performance; restore via infirmary/rest or Nerve Tonic *n* → 3n MP; maxima per BR-2.

**FR-QST — Quest (25) + global rules.** Global: **Mr. Filmon**, Chief of the Map Room at Terminus, is quest director — consult after each milestone. [D-1: veteran-greeting variant removed; canonical greeting: *"I choose you because Doctor Voss would never suspect you."*] Hidden **infamy counter** incremented by destructive acts (statue-smashing explicitly "monstrously infamous"); gates endgame dialogue and Lord Wood's availability [thresholds OQ-7 ⇒ §10].

- 001 Orientation: muster at Terminus chapter; buy/read folios (post-only) for brief.
- 002 The Map Room (D1, south of Terminus): east/center easy route + west corridor escalating set fights (ratling packs → Storm Brute/Basalt Colossus); folios II & III; curator's pantry (port-and-cheese room), waste-paper pit, weapon cupboard; hidden panels to treasure and to Mr. Filmon; warning sign *"Warning — Danger lies beyond."*
- 003 Resonator on its plinth (NW chamber): take → **bound Crystal Resonator**: *"The Resonator is bound to you now. You cannot put it down."* Undroppable, unsellable [elder lodestone BRIDGE].
- 004 Shrine: menu Inspect/Destroy/**Pray**/Leave. First Pray: elder shrine-intellect grants the Sun-Mind's Boon (usable in sites). Later Prays: gold. Destroy: infamy-flaggable desecration.
- 005 Halls of the Colossi (D2) penning: first entry sluices column into a numbered pen; escape via hidden panel; pens 3–6; *"KILMOR WAS HERE"*; first visit: Kilmor's starved body + blood-written journal (Folio I); revisit: bloodstain only. Never respawns.
- 006 Beast levers: six levers (1–6, 7=leave): 3 or 4 releases one penned horror; the other pits two to mutual death. [OQ-16 ⇒ fix dead-beast-wins edge silently.]
- 007 Wrestling pit: the keeper's challenge — face the **Ancient Bull Ape** bare-handed (no feats/devices/draughts; Accept/Refuse); entering zeroes expedition MP (warning shown); victory → vitality serum: **+1 CON whole column**, once [repeatability fixed: once, OQ-16-class fix].
- 008 Shuttered vault (SW room): without Sun-Key: dark force snuffs lights and ejects. With Sun-Key: key glows; proceed to claim the **Drowned Key**.
- 009 Booby-trapped cache: Blast → 2 smoke-marked gems, no trap; ease open → fume trap + 2 fine gems.
- 010 The funeral (D3), gated on Kilmor found: usher welcome; named guest rows (Lord Wood & Lady Katherine; Prelate Turak; Princess Charista & Prince Lefrod of the Lake-Folk; High Chief Argon; Pelzer the master bowyer; Scrub-Folk envoys; Kilmor's family and comrades; Mr. Filmon); taking seats triggers the rite: Voss's black-robed phantasm (mesmeric broadcast; thermal rays from emplaced devices) slaughters guests, warns the plateau to join him, fades. Afterward: charred bodies, empty chairs, casket ashes. Side encounters don't alter the script; corridor kills never log infamy.
- 011 Enclave warrens door: expedition contains Crag-Folk or Mesa-Folk → welcomed, opens; else *"Only crag-folk and mesa-folk are welcome below."* Hard gate [C-9: artisans' closed shop].
- 012 Feast & egg challenge: the Master Bowyer: take an egg from the giant viper without attacking or being attacked; **foul-smelling bottle = repellent (correct)**; sweet bottle = attractant (wrong → *"The air was bad. Come back later."*). Success → **the Old Master-Bow** (best non-elder bow); Great Beast pen hides a second top-tier bow; Lake-Folk huntress warns; corridor fights never turn the enclave hostile.
- 013 Old Mesmerist's price: Talk → *"an ancient and terrible rite"* for **all carried dollars + a measure of experience** → grants **#57**; revisit pre-use: *"You hold the Calling. You will know its hour."* Attacking triggers overlord/mesmerist combat.
- 014 Funicular Station (D5): wallcard *"Monday — Time-Space Reclamation. Tuesday — Matter-Energy Transference. Wednesday — the Sun-Ziggurat."*; coordinate plate *"Monday A7+ · Tuesday B7− · Wednesday C2+"*; collect **Sun-Key** (glowing key, cracked ceiling-lens chamber); Old Chronos (narcoleptic; advice tiers by progress: neither city / Sun-Ziggurat seen / Drowned seen → *"I cannot do anything else for you"*); his biscuit-mad pet drake (scratch/talk interactions, randomized purring, *"Remember — Chronos takes long naps."*). Operate: left spiral = glyph coordinates (letter A/B/C, digit 1–9, sign +/−); right spiral = Engagement Lever. **C2+ → ascend Sun-Ziggurat; C2− → descend Drowned Ziggurat.**
- 015 Sun-Ziggurat citadel (D6): crystalline sun-gate opens only to Sun-Key (unpickable/unbreakable); mirror-maze; three breakable crystal statues (a crag-folk elder, a lake-folk elder, an outlander — smashing = infamous act, each counts); glowing arches (warm vs scorching lens-ray); **Sun Priestess** (Leave/Attack/Talk — Talk works even after infamous acts): directs to the Drowned citadel, names the Drowned Key's location, notes mirrored layout (*"remember your steps"*); **Sun Gem** on a glass table.
- 016 Drowned Ziggurat citadel (D7): gate **Knock** → judged on infamy (clean barred / stained doubtful-worded, still barred / blackened: *"Enter, infamous ones."*) [OQ-7]; **Try the lock** → Drowned Key (voice notes Voss is not in). Mirror layout; wrong arch squares ~80+ HP all members. Break the **Obsidian Urn** (ledger variants "vase"/"jar" preserved) → scrambled plinth words; read **every fourth word** → Voss's invitation incl. *"…to find me, break the resonator upon the glyph-circle in my sanctum."* If no resonator: black statue of Voss holds one behind set fights; taking is overriding (*"…you cannot get rid of it."*). Red-chalk circle; center: *"Voss is not here."*
- 017 Glyph-circle menu (7 options): leave / place / turn thrice & wave / **break** / throw / wave & incant / wait → place/throw: won't leave the hand; wave/incant: concussion hurls column back; wait: nothing; **break: black void drinks the column → Ember Deeps level 2.**
- 018 Deeps transit: from Fumarole Camp, wind across lava patches (each crossing burns; resting to heal between crossings safe; standing on lava to heal doesn't re-burn); reach the Basalt Fastness. Heal before the fortress.
- 019 Lord Wood's War-Camp (D8): battle-noise approach; four set engagements to the command tent (larder/surgery/quarters/munitions; rich matériel cache; stockade beast-pens for optional fights). Not infamous: Wood delivers **Folios V & XIV** + endgame plan (find the Fastness in the Deeps; perform #57 before Voss to open his ether-gate; if lacking #57 → go to the Hidden Enclave; repeats: *"I will repeat the plan."*). **Infamous: *"There is no one here."***
- 020 Filmon's staging spine (order enforced): rescue Kilmor → funeral → Sun Priestess → find Drowned citadel → meet Wood at War-Camp → meet Wood in the Fastness. Repeat prefix: *"Listen to Mr. Filmon of Terminus Post."*
- 021 Voss's Basalt Fastness (D9): hidden-panel maze; set encounters (viper-moths, ether-phantoms, basalt colossi, tyrant kings, high fiends; cold-spot *"a lifeless chill"*; cracked-panel *"a hideous laugh"*; a weaving route through concealed panels avoids every set engagement). Center sanctum: **Doctor Voss**, calm. Menu: **Fight / Talk / Perform a feat.**
- 022 Climax: Talk branches [OQ-7]: pure → *"You are too pure and good for me. Prepare to die, fools."*; stained → *"…prove yourselves truly infamous by defeating Lord Wood."*; blackened → *"…defeat Lord Wood, and kneel to me."* Perform: wrong feat/unknown → *"no noticeable effect at this distance."* **#57:** black gate opens; Lord Wood enters: psychic duel set piece (blue arc, smoke, charring — preserved wording, RS-8); choice **Fight Lord Wood** or **Fight Doctor Voss**. With #57 performed, **Voss is flagged Hollowed** → Counter-Talisman Rites effective against him; otherwise normal menace.
- 023 Endings: *Good* (Voss defeated): the **Sun-Mind** congratulates the column's goodness: *"You kept faith with the Light. The Plateau remembers its friends."* *Evil* (Wood defeated): the **Drowned Mind** congratulates infamy and urges them to spread it: *"You have the makings of an apostle of the Deep. Go out, and teach others your ways."* ; Voss prevails. Both award equipment and experience [table OQ-18 ⇒ §10]; **play continues; world unchanged.**
- 024 The Hermit's Shack (D10, optional): two broth bowls — one attribute (STR/INT/DEX/CON/CHA) chosen per sitting, all present members same type, two bowls total ever, now or later; reveal: the hermit is Voss (glamour), invites the column to join him; +2 total to chosen attribute for the column [mechanics OQ-10 ⇒ §10]; **once per party — does not reset with site.**
- 025 The Drake Hollows (D11, optional): escalating saurian fights (drake pup → yearling → bull drake → tyrant king), four magnitudes; escalating hoards; flavor per stash: *"You have found a drake's trove."*

**FR-SAV — Persistence (4).** · 001 Post-only manual save; autosave on every post exit; mid-expedition quit resumes at last post. · 002 Site-state save on exit (player choice); saved-vs-original choice on re-entry; one-time items never re-created. · 003 Backup/restore members to separate storage via utilities; new-game reset requires explicit erase-confirmation. · 004 Historical variance (roster-number prompt, reboot-restore, menu save file) is packaging — one canonical model per FR-SAV-001/002 [§10 ADR-4].

**FR-UIX — Presentation & configuration (3).** · 001 Screen layout: top per-member panel (name, profession, MP cur/max, HP cur/max, body diagram, status); center-left messages/terrain; center-right menace ranks/status in combat; bottom-left area map (trail always mapped; site progressive); bottom-center current menu; bottom-right figures view. · 002 Input: numbered menus take digits; lettered options take bracket letter; two-choice by first letter; Y/N; RETURN continues; members referenced by column number 1–6 outside roster lists; movement N/E/S/W plus 3-E-S-W diamond on keyboards lacking arrows; pointer optional [C-2: keyboard-only v1, pointer deferred]. · 003 Playback: time lag 0 (fastest)–9 (slowest) canonical; sound on/off canonical and **functional** [C-5/D-2: no audio emitted]; three-speed selector rejected as packaging.

### 2.3 Business Rules (verbatim where tabulated; BR-14…BR-29 carry no entries in the sealed register — numbering preserved, absent numbers are non-requirements)

**BR-1 — Hit points by profession/level (base, CON 10; levels 1–15) `[REQ verbatim]`**

| Profession | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| White Hunter | 10 | 20 | 32 | 44 | 56 | 70 | 82 | 94 | 106 | 120 | 130 | 140 | 150 | 160 | 170 |
| Scout | 8 | 18 | 28 | 40 | 50 | 60 | 72 | 84 | 96 | 110 | 120 | 130 | 140 | 150 | 160 |
| Expedition Doctor | 8 | 12 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 98 | 106 | 114 | 122 | 130 |
| Pugilist | 8 | 10 | 18 | 22 | 32 | 44 | 54 | 62 | 70 | 80 | 88 | 96 | 104 | 112 | 120 |
| Cat Burglar | 6 | 10 | 18 | 22 | 32 | 40 | 48 | 54 | 60 | 70 | 78 | 86 | 94 | 102 | 110 |
| Antiquarian-Mesmerist | 6 | 8 | 12 | 16 | 22 | 28 | 34 | 38 | 44 | 50 | 56 | 62 | 68 | 74 | 80 |

CON≠10 scaling: `[REQ]` says "base, CON 10" → scaling rule [P]: ±5% of tabulated max per CON point above/below 10, rounded down, applied on training. Levels 16–20 [P, OQ-2]: extend by the profession's level 13→15 increment (+10/+10/+8/+8/+8/+6) → WH 180–220, Scout 170–210, Doctor 138–170, Pugilist 128–160, CB 118–150, AM 86–110.

**BR-2 — Maximum MP by profession/level (1–15) `[REQ verbatim]`**

| Profession | 1 | 5 | 10 | 13 | 15 |
|---|---|---|---|---|---|
| Antiquarian-Mesmerist | 10 | 13 | 16 | 18 | 20 |
| Expedition Doctor | 10 | 14 | 19 | 20 | 20 |
| Scout | 8 | 12 | 17 | 18 | 19 |
| Pugilist | 10 | 11 | 13 | 16 | 20 |
| White Hunter | 7 | 9 | 12 | 15 | 18 |
| Cat Burglar | 6 | 8 | 12 | 14 | 15 |

Intermediate levels [P]: linear interpolation between documented anchor pairs, rounded to nearest. Levels 16–20 [P, OQ-2]: frozen at level-15 values.

**BR-3 — Attributes `[REQ verbatim]`.** Five attributes, range 3–22 at creation; profession modifiers (STR/INT/DEX/CON/CHA): White Hunter +2/−2/+1/0/−1; Pugilist 0/0/+1/0/0; Expedition Doctor 0/+2/0/0/0; Scout 0/+1/0/0/+1; Cat Burglar −2/0/+2/0/−1; Antiquarian-Mesmerist −4/+3/+2/0/+1. Luck 8–13. Strain maxima [GUARD framing: physiology]:

| Strain | STR | INT | DEX | CON | CHA | | Strain | STR | INT | DEX | CON | CHA |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Club Stock | 18 | 18 | 18 | 18 | 18 | | Ratling | 17 | 15 | 19 | 19 | 13 |
| Crag-Folk | 20 | 17 | 17 | 19 | 17 | | Sauroid | 19 | 14 | 17 | 18 | 13 |
| Lake-Folk | 17 | 19 | 19 | 17 | 18 | | Ape-Man | 20 | 14 | 16 | 19 | 12 |
| Mesa-Folk | 19 | 17 | 18 | 19 | 17 | | Basalt Brute | 21 | 14 | 16 | 19 | 13 |
| Scrub-Folk | 16 | 18 | 20 | 18 | 17 | | Fen-Man | 19 | 16 | 17 | 18 | 14 |
| Hyena-Man | 20 | 13 | 17 | 21 | 11 | | Glider-Folk | 16 | 18 | 21 | 16 | 17 |
| Albino Tunnel-Folk | 17 | 14 | 18 | 17 | 11 | | Wing-Folk | 16 | 18 | 22 | 16 | 17 |
|  |  |  |  |  |  | | Long-Man | 22 | 13 | 15 | 20 | 12 |

**BR-4** XP thresholds depend on strain/attributes/profession [OQ-3 ⇒ §10]; training bought from treasury [OQ-4 ⇒ §10]. **BR-5** 3 trainings/level; same-skill repeats diminish. **BR-6** Feat slot limits by profession/level/INT [matrix OQ-5 ⇒ §10]. **BR-7** Ceilings: treasury ≤ 65,000 canonical; credit lines ≤ 65,000 each; deposit fee per deposit; shares 1/2/3 apportioned with round-down (preserved exemplar: $6,000 across 6 members ⇒ $999 each). **BR-8** ≤9 items/member; ≤90 found undistributed; exactly 1 weapon, 1 shield, 1 armor, 1 Fire piece in use. **BR-9** Prerequisites: armor/shield → STR; bows/rifles → STR+DEX; melee → 2×STR+DEX; elder-work has **lower** prereqs at equal point value; insufficient ⇒ Unusable (carryable, not wieldable). **BR-10** Radium Tonic *n* → *n²* HP + BR-30 cure; Nerve Tonic *n* → 3*n* MP. **BR-11** Post infirmary free; rest-house $250 +tax; typical wilderness bribes ≈$250. **BR-12** Per-kill XP ≤ 65,535 canonical (divergent boss figures preserved as notes only). **BR-13** Thrust = 1 swing best accuracy +1–2 dmg; Attack = 2; Slash = 3–4 reduced accuracy −1–2; fallbacks per FR-CMB-002. **BR-30** Tonic 1–3/Suture I: 1 injury; 4–6/II: 1 break or 2 injuries; 7–9/III: 1 gone-area (or equivalents); 10/IV: >1 gone. **BR-31** Death at 0 HP or head/torso Gone; Revivification CON −1..2; Tribunal returned = −carried dollars, −1 CON; Hollowed = level 20, frozen. **BR-32** Menace manifest: 78 types with pack max, HP, mummified flags, treasure, XP; unique bosses (Ancient/Great Bull Apes, Sun Priestess, Boo Boo Kitty — a pampered giant sabre-tooth, Doctor Voss two forms one flagged Hollowed, Lord Wood). **BR-33** World metrics: overworld 75×50 (25 sectors A–E × I–V); ziggurat maps 18×9 ×2; Deeps 30×15 w/ lava course; sites 30×24 ×11; 17 posts; 8 rest-houses; ~15–16 folio texts. **BR-34 Hard gates:** funeral ⇐ Kilmor found; SW Colossi chamber ⇐ Sun-Key; Sun-Ziggurat gate ⇐ Sun-Key; Drowned gate ⇐ Drowned Key **or** sufficient infamy; Enclave warrens ⇐ Crag-Folk/Mesa-Folk member; Wood's audience ⇐ not infamous; endgame ether-gate ⇐ #57. **BR-35** Crystal Resonator bound/undroppable/unsellable; reissued at Drowned citadel black statue if never collected; breaking at glyph-circle = only route to Deeps. **BR-36** One-time events/items never respawn, including under site reset. **BR-37** Passive feats counter opposing actives; actives cumulative except Sleep (no deepening) and progressive families; Dread stacks.

### 2.4 Data Registries (mandate; exhaustive rows land in Doc 2 §5 — placement map in §5.7 here)

- **R-1 Equipment:** 20 shields (point 1–20; req = point STR; hide shields → boiler-plate bucklers), 20 field armors (point 1–11 scale; Elder Lamellar god-tier), 20 Fire pieces (point 1–20, STR+DEX ladder — each rung = one bow & one express-rifle skin, one value [RS-1]), 40 melee (point 1–25; 2×STR+DEX; master-work lines Hunting Knife/Cudgel/Flail/Hunting Spear/Cavalry Sabre/Pole-axe +N; Sun-Metal Knife / Cudgel-equivalent Mace / Sun-Metal Sabre; elder-work prereq discount per BR-9).
- **R-2 Tonics/folios/valuables:** 10 radium + 10 nerve; 20 folio items → 15 texts + XVI sealed [OQ-12]; 40 valuables incl. quest uniques (Sun-Key, Drowned Key, Sun Gem, Obsidian Urn, Crystal Resonator, Old Master-Bow).
- **R-3 Strains/professions/skills:** per §III above; professions-balance guidance preserved as flavor text only.
- **R-4 Feat registry:** full 56-row table in §5.4 (closure arithmetic shown there); #53 vacant; #57 The Calling; #58 Sun-Mind's Boon [OQ-1]; documented anchors: #1–4 Sutures; #5 Thermal Lancet 1; #13 Incendiary Loads 1.
- **R-5 Folio texts:** 15 payloads mapped to canon slots: I Kilmor's Testament; II History of the Cradle; III The Tribunal of Voices; IV The Crystal Resonator; V News of the Long War (Lord Wood); VI The Master Bowyers; VII The Twin Cities; VIII The Map Room; IX The Halls of the Colossi; X The Crag-Folk Vaults; XI The Mesa Enclave; XII The Funicular Station; XIII The Sun-Ziggurat; XIV The Basalt Fastness; XV The Man Who Heard the Drowned Mind; XVI sealed/illegible. Payload prose = narrative-author-of-record texts re-authored to canonical nouns by **topic match** (Bible numbering ≠ canon numbering; matching table in Doc 2 §5).
- **R-6 Menace table:** 78 types (families incl.: Desiccated Sentinel[M], Drake, Colossus, Fiend, High Fiend, Blood-Wraith[M], Ether-Wraith[M], Renegade Medium, Hooded Illusionist, Enclave Mesmerist, Cult Hierophant, mummified acolytes[M], Hyena-Man/Ratling/Sauroid raiders, megafauna, insect/slime, saurids…), tiers Low→Very High, dispositions Placid/Wary/Savage; full rows Doc 2 §5. [M] = mummified flag.
- **R-7 Geography:** province 75×50 with post/rest/site coordinates (17 posts incl. Sun-Terrace Station, Lake-Bottom Post, Fumarole Camp; 8 rest-houses: Deadfall Rest, Crown Rest, Portage House, Mirage Rest, Badlands Rest, Campfire Rest, **Royal Rest** [OQ-14 canonical; "Jolly Rest #1" anomaly retired], Jolly Rest); ziggurat maps; Deeps lava course. Coordinates grid: Doc 2 §5.
- **R-8 Site scripts:** per-site square scripts, room labels, encounter assignments for the 11 sites (Map Room; Halls of the Colossi; Crag-Folk Burial Vaults; Hidden Enclave; Funicular Station; Sun-Ziggurat citadel; Drowned Ziggurat citadel; Lord Wood's War-Camp; Voss's Basalt Fastness; Hermit's Shack; Drake Hollows), reproduced functionally per FR-QST + script DSL (§6.4); full grids Doc 2 §5.

### 2.5 Non-functional requirements `[REQ §VI]` + operator NFRs

1. Save granularity per C-10. 2. Sessions begin/end in posts. 3. Time lag 0–9, sound toggle (C-5). 4. Monetary ceilings per BR-7. 5. Aging observable (cross-province retrieval ≈2 months ⇒ §10 OQ-6 cadence). 6. Capacity: roster envelope "dozens" (guaranteed floor 21 slots incl. 3 automata — canonical model fixes **30 total slots**: 27 members + 3 automata [P, within envelope]); expedition 6; 9 items/member; 90 found items; score 0–100. 7. No network/multiplayer/difficulty setting; grind-mitigation by menace tiers scaling with distance from Terminus. 8. Demo/attraction reel at boot. Plus: determinism C-3; headless completability; both-endings golden campaigns (A-2); defect-free zero-context buildability (SC-1).

### 2.6 Deviations `[D]`

**D-1** [OD-3]: FR §VII-1 removed; FR-SES-004 transfer branch removed; FR-QST Filmon veteran greeting removed (single canonical greeting). **D-2** [OD-7]: FR-UIX-003 sound toggle shipped functional; zero audio output v1. Both traced in §10 ADR-9/10.

---

## 3. System Architecture

Three layers, strictly one-way data flow [C-6]:

```
┌──────────────── 1. SIMULATION CORE ────────────────┐
│ pure Python, glyph-free, deterministic (C-3)       │
│ GameState aggregate → command verbs → events       │
└──────────────┬──────────────────────────▲──────────┘
        frames + events (DTOs)      commands only
┌──────────────▼──────────── 2. DISPLAY MODEL ───────┐
│ 120×40 logical frame of cells; each cell = ordered  │
│ layer stack {symbol_id, fg token, bg token, flags}  │
│ symbol dictionary resolves ids → CP437 glyph/tile   │
│ menus declared as data; screens composed by region  │
└──────────────┬──────────────────────────▲──────────┘
         cell batches                key events
┌──────────────▼──────── 3. RENDERER (swappable) ────┐
│ TextRenderer v1: python-tcod, CP437 sheet, 120×40   │
│ (Future) TileRenderer: same frame + dictionary,     │
│ dictionary extended with sprite column — sim blind  │
└─────────────────────────────────────────────────────┘
```

**Rules that make the swap safe (architecture invariants):** logic never reads the display grid back [C-6]; no magic characters in game code — glyphs exist only in the dictionary; one logical entity per cell in the text era, but positions/state are entity-level so tiles can interpolate later [C-6]; everything a tile artist would restyle is data (symbols, color tokens, item/menace definitions, menu descriptors, dialogue text) [C-6]; animation timestamps: simulation events carry tick stamps in the event stream so a future presentation layer may interpolate without sim changes.

**Module map (packages):**

- `engine/` — Simulation Core. `state` (GameState aggregate), `rng` (seeded PRNG port + log), `commands` (verb dispatch), subsystems: `roster`, `creation`, `training`, `credit`, `outfitter`, `infirmary`, `timekeep` (aging), `trail` (wilderness), `sites` (maps/traps/panels/locks), `encounters` (warden/morale), `combat`, `feats`, `body`, `quests` (Filmon spine, infamy, endings), `tribunal`, `persistence` (snapshot in/out). No I/O to screen; persistence writes via injected file port.
- `content/` — authored JSON registries: R-1 items, R-2 tonics/folios/valuables, R-3 strains/professions, R-4 feats, R-5 folio texts + dialogue, R-6 menaces, R-7 geography (maps as data), R-8 site scripts (DSL), plus `symbols.json` (symbol dictionary), `menus.json` (menu descriptors), `strings` (all text; C-8/C-9 linted).
- `ui/` — Display Model: `frame` (cell/frame types), `composer` (six regions per FR-UIX-001), `symbolmap` (id→glyph resolution, state variants), `colors` (semantic token table), `menukit` (renders/executes menu descriptors → commands), `inputmap` (keys per FR-UIX-002).
- `render/` — `text_renderer` (tcod console, CP437 font, integer scaling), `tile_renderer` (future; interface only).
- `platform/` — `main` (**composition root**: constructs registries, PRNG, state, engine, composer, renderer, input loop; no other module constructs infrastructure), `saveio` (JSON slot files, backup/restore), `config` (window scale, time-lag default, sound toggle persistence), `boot` (attract reel script playback).

**Primary runtime paths** (traced exhaustively in Doc 2 §15): boot→menu→new/continue/demo/utilities; chapter loop (recruit/muster/train/learn); post loop → leave post (autosave) → trail traversal (terrain/swim/menace/night-camp) → encounter → melee rounds → spoils → site exploration (look/doors/panels/traps/scripts) → exit (site-state save) → return to post (XP divide, services, save); quest driver consults Filmon after milestones; total-wipe → Tribunal; ending paths via glyph-circle → Deeps → Fastness → #57 → choice → ending.

**State residence:** all game state lives in the single `GameState` aggregate inside the engine process; the display model holds a read-only frame projection; the renderer holds nothing but the window. Persistence is a snapshot of `GameState` + PRNG state [C-3/C-4]. No state crosses a process boundary except via save files and backup copies.

---

## 4. Component Responsibilities

| Component | Responsibility | Consumes | Produces |
|---|---|---|---|
| `engine.state` | Single mutable world aggregate; invariants (BR-8 capacities, BR-34 gates, BR-36 one-time flags) | commands | events; snapshot |
| `engine.rng` | One PRNG; every random draw logged; state serializable into save | seed (composition root) | all rolls |
| `engine.combat` | Round orchestration, tactics validation, fallbacks, ballistics, statuses, morale handoff, spoils | menus selections | round events; XP/$ |
| `engine.encounters` | Contact sequence, random menaces by terrain, night camp, surrender/parley/mercy/flee | trail/site position; disposition data | combat instance or resolution |
| `engine.feats` | Registry-driven effects; domain/class checks (BR-37); MP economy | feat id, performer, target | effects/counters |
| `engine.quests` | Filmon staging order; infamy counter & tiers [OQ-7]; gating (BR-34); ending branch | world flags | dialogue/gate decisions |
| `engine.timekeep` | Calendar, travel costs [OQ-6], aging decay | movement/rest events | age/attr drift |
| `engine.tribunal` | Total-wipe per-member judgement [OQ-11] | dead expedition | returned/Hollowed |
| `engine.persistence` | Snapshot ↔ JSON DTO; site original/saved/original-restore choice | state | save document (to `platform.saveio`) |
| `content/*` | All registries/scripts/strings/symbols/menus as versioned data files | — | validated registries at load |
| `ui.composer` | Builds 120×40 frame from events+state projection; six regions | state projection | frame |
| `ui.symbolmap` | symbol_id→glyph/state/color resolution via dictionary | frame | concrete cells |
| `ui.menukit` | Interprets menu descriptors; validates input; emits commands | key events | commands |
| `render.text_renderer` | Blits cells, polls keyboard, scales window | cells | key events |
| `platform.main` | **Composition root** — constructs and wires everything; owns game loop | config | running app |
| `platform.saveio` | Slot files, autosave, backup/restore, erase-confirm | DTO | files; schema validation on load |

---

## 5. Data Model

### 5.1 Entities & invariants

**Adventurer:** strain (5+10 enum), profession (6), standing (4), attributes STR/INT/DEX/CON/CHA (3–22, strain-capped), Luck 8–13, Age, Level (≤20 [OQ-2]), XP, HP cur/max, MP cur/max, Skills[9] %, FeatsKnown[] (+learnable slots), items[≤9] (+4 in-use slots per BR-8), credit balance, quest-progress score contribution, resident post, Body[6]×{Okay,Injured,Broken,Gone}, VitalStatus {Okay, Sleeping, Down, Unconscious, Dead, Hollowed}. Infamy is expedition-level, never per-member.

**Club:** roster of members (canonical model: 30 slots = 27 members + 3 reserved automata [P within "dozens" envelope]), resident post per member. **Expedition:** 1–6 members + ≤1 summoned automaton (combat only); Treasury ($≤65,000 [ADR-5]); FoundItems[≤90]; infamy counter; quest score 0–100; current location (map id, x, y); time out of post.

**Item:** 180 identities / 8 families: Shields 20, Field Armor 20, Fire pieces 20 (bow|rifle skins per rung), Melee 40, Radium tonics 10, Nerve tonics 10, Folios 20, Valuables/quest 40. Fields: point value, attribute prerequisite, flags {elderWork, bound, unique/oneTime}. Items never lost/stolen/destroyed except beg-for-mercy tribute and feat-listed exceptions.

**Feat:** id 1–58 (#53 vacant), name, MP cost, domain, class {Passive|Active(+family exceptions)}, effect spec. **Post:** 17 (Terminus Post #1, Salt Landing, Pendry's Ferry, Rockfell Camp, Delta Post, Tamarisk Mission, Tiernan's Landing, Anvil Camp, Serein Mission, Xavier's Drift, Flagler Station, Lansing Post, Scandia Port, Schatika Post, Sun-Terrace Station, Lake-Bottom Post, Fumarole Camp); identical services each. **RestHouse:** 8 (§2.4 R-7 names). **Maps:** Province 75×50 (sectors A–E/I–V); Sun-Ziggurat 18×9; Drowned Ziggurat 18×9; Deeps 30×15 w/ lava; Sites 30×24 ×11. **Site:** original vs saved state; one-time flags. **MenaceType:** 78 rows {packMax, HP, gear/feats, mummified flag, treasure, XP, tier, disposition}; menace instance: rank, status K/S/U/D, body[6].

**QuestState:** milestone per FR-QST-020 order; infamy {0=pure,1–2=stained,≥3=blackened} [OQ-7]; once-ever flags (Kilmor→bloodstain, funeral→charred chairs, hermit broth 2 bowls, shrine granted, statues smashed[3], urn broken, resonator held/issuer…). **WorldClock** day counter.

### 5.2 Lifecycles

- **Adventurer:** Created → Rostered ⇄ Expedition → Dropped(post-pinned) → Purged(terminal); Dead → Revivified(CON −1..2) | Tribunal → Returned(−$, −1 CON) | Hollowed(level 20, frozen) [BR-31; OQ-11: Hollowed irreversible].
- **Body location:** Okay → Injured → Broken → Gone; cured per BR-30/FR-BOD-003.
- **Site:** Original → Explored/Saved ⇄ Revisited (re-trap/re-man possible; quick revisit retains dead) → Restore-Original (one-time content **not** restored) [BR-36].

### 5.3 Canonical noun register (mechanics-facing; strings registry per C-8/C-9)

Currency: **dollar ($)**. Services: Post infirmary / Letter-of-credit counter / Outfitter / Debrief officer / Rest-houses. MP = mesmeric potency (one pool; abstracts charge/draught/stamina). Planes: Province / Sun-Ziggurat / Drowned Ziggurat / Ember Deeps / Séance Tribunal. Elder intellects: Sun-Mind / Drowned Mind. Automata: Mud-class (Mark I Earthmover), Mist-class (Mark II Shroud), Air-class (Mark III Gyro); summons = Hangar Dispatch. Menace family renames: Skeleton→Desiccated Sentinel; Dragon→Drake; Giant→Colossus; Demon/Devil→Fiend; Vampire→Blood-Wraith; Wraith→Ether-Wraith; undead flag→**mummified** (menaces) / **Hollowed** (members, Tribunal Voss flag). Skills: ninth = **Marksman**. Full string-level registry (all remaining flavor nouns): Doc 2 §5.

### 5.4 R-4 Feat registry (complete; `[REQ]` anchors + `[P]` unquoted cells)

Row-closure note `[P]`: quoted "1–4" tier labels exceed free rows; resolved as — Confusion keeps 4 rows; **Enervation and Paralysis take 3 rows each** (tier labels 1/2/4 by MP cost); Vitriol Projector fills the 37–40 body-area band; all quoted figures unchanged elsewhere. #53 vacant [OQ-13].

| # | Feat | MP | Domain | Class | Effect |
|---|---|---|---|---|---|
| 1–4 | Suture 1–4 | 1–4 | Everywhere | Active | Heal 1–9 / 1–27 / 1–57 / 1–99 HP + body cure BR-30 tiers I–IV `[REQ]` |
| 5–8 | Thermal Lancet 1–4 | 1–4 | Combat | Active | 1–10/1–30/1–60/1–100 to one menace body area `[REQ]` |
| 9–12 | Thermal Sweep 1–4 | 1–4 | Combat | Active | 1–7/1–15/1–31/1–66 to **every** menace, armor-mitigated `[REQ]` |
| 13 | Incendiary Loads | 1 | Combat | Passive | Self: +50% accuracy, +15 Fire point value `[REQ]` |
| 14 | Party Incendiary | 2 | Combat | Passive | Column-wide 13 `[REQ/P]` |
| 15 | Express Loads | 3 | Combat | Passive | Self: +100%, +25 `[REQ]` |
| 16 | Marksman's Trance | 1 | Combat | Passive | Self Marksman → 250 `[REQ]` |
| 17 | Party Trance | 3 | Combat | Passive | Column-wide 16 `[P]` |
| 18–21 | Adrenal Surge 1–4 | 1–4 | Combat | Passive | +10/25/45/70% speed; counters Slow `[REQ]` |
| 22–25 | Nerve-Hardening 1–4 | 1–4 | Combat | Passive | +1/3/6/10 armor each member `[REQ]` |
| 26 | Mesmeric Charm | 2 | Combat | Passive | Menaces friendly until attacked `[REQ]` |
| 27 | Mesmeric Sleep | 1 | Combat | Active | Sleep (no deepening) `[REQ]` |
| 28 | Mesmeric Dread | 2 | Combat | Active | Fear (stacks) `[REQ]` |
| 29–32 | Mesmeric Confusion 1–4 | 1–4 | Combat | Active | Impedes enemy feat use; progressive `[REQ]` |
| 33–36 | Mesmeric Assault 1–4 | 1–4 | Combat | Active | 1–5/1–11/1–41/1–81, HP only `[REQ]` |
| 37–40 | Vitriol Projector 1–4 | 1–4 | Combat | Active | Specific body area; dice `[P]`: 1–12/1–35/1–70/1–120 |
| 41 | Enervation 1 | 1 | Combat | Active | Reduces menace damage; progressive `[REQ]` |
| 42 | Enervation 2 | 2 | Combat | Active | ↑ |
| 43 | Egress | 3 | Combat | Active | Escape combat `[REQ]` |
| 44 | Revivification | 4 | Everywhere | Active | Revive dead; CON −1..2 `[REQ]` |
| 45 | Enervation 4 | 4 | Combat | Active | ↑ |
| 46 | Paralysis 1 | 1 | Combat | Active | Inhibits movement, easier to hit; progressive `[REQ]` |
| 47 | Paralysis 2 | 2 | Combat | Active | ↑ |
| 48 | Hangar Dispatch | 3 | Combat | Active | Calls pre-designated automaton (FR-CHR-008) `[REQ]` |
| 49 | Counter-Talisman Rites | 1 | Combat | Active | Mummified flee or crumble `[REQ; OQ-17 MP=1]` |
| 50 | Paralysis 4 | 4 | Combat | Active | ↑ |
| 51 | Awaken | 1 | Combat | Active | Rouse sleepers / neutralize Sleep `[REQ]` |
| 52 | Field Assessment | 1 | Combat | Passive | Approximate menace level; occasionally wrong `[REQ]` |
| 53 | — vacant — | — | — | — | Unlearnable [OQ-13] |
| 54 | Supply-Line Recall | 4 | Everywhere | Active | Post-to-post travel, cross-planar `[REQ]` |
| 55 | Pugilist's Trance 1 | 3 | Combat | Passive | Superhuman attack/defense/damage `[REQ]` |
| 56 | Pugilist's Trance 2 | 2 | Combat | Passive | **Stronger than T1 at lower MP — quirk preserved** `[REQ]` |
| 57 | The Calling (elder rite) | 4 | Combat | Active | In Voss's presence: opens ether-gate; Lord Wood enters `[REQ; OQ-1 MP4 P]` |
| 58 | Sun-Mind's Boon (elder rite) | 4 | Site | Active | Full-party heal + infirmary-strength body cure; granted once (FR-QST-004) [OQ-1 P] |

### 5.5 Equipment ladder schemas (anchors `[REQ]`; full 180-row tables `[P]` → Doc 2 §5)

Shields: rung *v* (1–20) ⇒ req STR *v*, value *v*; names progress hide→boiler-plate buckler. Armor: value 1–11, STR req by value; Elder Lamellar = value 11 god-tier. Fire pieces: rung *v* (1–20) ⇒ bow-skin + rifle-skin, one value/prereq (STR+DEX) — rifles inherit bow ballistics [RS-1]. Melee: value 1–25 ladder; req = f(2×STR+DEX); master-work +N lines and Sun-Metal lines listed per §2.4; **elder-work: prereq at ⌈⅔ base⌉ per value, listed best→worst** [BR-9 P-concretization].

### 5.6 Menace schema & balance rule

Row: `{id, name, familySymbolId, packMax, HP, gear[], featList[], castsPerCombat, mummified, treasureTable, xp, tier(Low|Med|High|VeryHigh), disposition(Placid|Wary|Savage), regionFloor (min distance-band from Terminus)}`. Balance rule [OQ-19 P]: effective menace HP/damage scale with sector distance-band B (1–5): HP ≈ 8×B×tierMul; caster repertoires [OQ-8 P]: each caster type = one offense line (Lancet/Sweep/Assault by tier) + one control (Sleep/Dread/Enervation); casts/combat = 2/3/4/5 by tier; cast-instead-of-melee chance = 50%. Full 78 rows → Doc 2 §5.

### 5.7 Registry placement map (SC-1)

Doc 2 §5 holds exhaustive tables: item ladders (§2.4 R-1 + §5.5 schemas), tonic/folio/valuable rows + folio full texts (canonical-topic match table), strain/profession/skill starting tables (§10 OQ-20), feat-availability matrix (§10 OQ-5), menace 78 rows (§5.6 rule), R-7 coordinate grids (ASCII), R-8 site scripts (DSL instances), complete dialogue string registry, symbol dictionary rows, menu descriptors.

---

## 6. API & Interface Design

No external network interfaces exist [C-7]. Internal contracts:

**6.1 Engine command interface.** All verbs flow as commands (this list is also the menu contract): session {new, continue, demo, utilities{backup, restore, erase-new}}; chapter {recruit{strain, profession, accept/reject}, list, purge, add, drop, rename, designate-automaton, train, learn-feat}; credit {withdraw, deposit}; outfitter {list, continue-list, buy, sell}; post {debrief, infirmary, use-feat, use-item, distribute, trade, inspect, save, leave}; trail {move(dir), perform-feat, inspect, use-tonic, config}; site {move, look, listen-respond, pick-lock, disarm, leave, choose-menu options}; encounter {fight, accept-surrender, parley, beg-mercy, flee}; combat per member {thrust, attack, slash, lunge, aim, feat(id,target), parry, fire(rank), other{rank, timelag, sound}, redo}. Every command returns events (typed, tick-stamped).

**6.2 Frame contract (sim → display):** `Frame { width:120, height:40, cells[40][120]: { layers[ {symbol_id:int, fg:token, bg:token, flags} ] }, menus[], messages[], dirty-tick }`. symbol_id 0–255 = CP437 literals (UI text/borders); ≥256 = entities via dictionary:

```json
{ "hyena_man": { "glyph": "h", "fg": "hide", "states": { "mummified": { "fg": "ash" } } },
  "wall_basalt": { "glyph": 219, "fg": "stone_dark" },
  "corpse_generic": { "glyph": "%", "fg": "blood" } }
```

Color tokens are semantic (`blood`, `ash`, `stone_dark`, `lsd_glow`…), restyleable; renderer resolves to RGB.

**6.3 Save document (C-4):** `{ schema_version, rng_state, clock, roster[], expedition{…}, world{ site_states, one_time_flags, infamy, milestone }, treasury, resident_posts, config_echo }`; site original snapshots embedded in content data, saved deltas in save doc; backup/restore = slot-file copy with schema validation.

**6.4 Site script DSL (R-8):** declarative triggers: `{ at:[x,y], on:enter|menu|flag, if:{flags, items, infamy-tier, strain-present}, then:[ msg, menu, combat(set-id), give(item), set-flag, transport(map,x,y), damage, mp-zero, … ] }` — every FR-QST set piece expresses in this vocabulary; the DSL verb list is closed in Doc 2 §5.

**6.5 Input map (FR-UIX-002, C-2):** arrows + W/A/S/D-free diamond: numeric-pad 3/E/S/W fallback; digits menu; bracket-letter; Y/N; ENTER=RETURN-continue; ESC=leave/back where a Leave option exists. **6.6 Demo mode:** boot-menu selection plays a recorded command script against a fresh seeded state through the normal display path (A-1).

**6.7 Backup format:** same JSON as save, member-scoped export `{schema_version, member{…}}` [FR-SAV-003].

---

## 7. Security Architecture

Local single-player; no secrets, accounts, or network [C-7]. Residual measures: (1) all file loading (saves, backups, content) schema-validated and range-checked before use — malformed input yields an observable load error, never a crash or state mutation; (2) JSON parsing only — no `eval`/pickle anywhere (arbitrary-code-exec prevention)； (3) backup/restore filenames sanitized to slot identifiers (no path traversal); (4) save tampering is out of threat model (hex-editing legacy "cheat" is excluded as a defect, not defended); (5) content content-lint (C-8 magic ban, C-9 register check) runs at build/CI time, not runtime.

---

## 8. Infrastructure & Deployment

Single desktop process [C-7]: Windows/macOS/Linux via SDL2 (bundled by python-tcod wheels) [C-1]. Runtime deps: Python 3.12, `python-tcod` (pinned in Doc 2 §3), stdlib only otherwise. Assets: bundled CP437 font sheet; content pack JSON directory (read-only at runtime). Build: `pip install -e .` dev flow; distribution via PyInstaller one-folder bundle (A-4; late build step). Resource envelope trivial: <200 MB RAM, 960×640 base window × integer scale; any 2015+ hardware. No services, schedulers, installers, or updates.

---

## 9. Operational Model

**Sessions:** begin/end at post menus [C-10]; autosave slot written on every post exit (FR-TWN-005); manual save slots at post menus; Continue resumes at recorded post. **Slots:** fixed layout — slot 0 autosave, slots 1–4 manual, plus backup directory [P]; quit mid-field resumes from last autosave (FR-SAV-001). **New game:** explicit erase-confirmation flow (FR-SES-004). **Demo:** attract reel idle after N sec at boot menu and via menu entry [P N=60]. **Time-lag/sound config** persisted in config file (separate from saves), default lag 4 [P], sound toggle ON-but-silent honored (D-2). **Crash behavior:** uncaught exception → incremental rollback marker in debug log file (off by default; `CRADLE_DEBUG=1` enables) [P]; player recovers via Continue. **Observability (dev/test):** RNG draw log + event log replay for golden runs [C-3]; no telemetry.

---

## 10. Key Design Decisions

**ADR-1 [OD-2]** Three-layer split with symbol dictionary and frame contract; simulation glyph-free. Consequence: tile swap later = new renderer + dictionary sprite column only. **ADR-2 [OD-5/C-3]** Determinism: one `random.Random(seed)` injected at root; every subsystem draws via engine.rng; save stores PRNG state; event log enables golden replays and headless acceptance (A-2). **ADR-3 [C-6]** Content-as-data: all registries, maps, scripts, menus, strings, symbols in versioned JSON; engine contains zero content constants. **ADR-4 [FR-SAV-004]** Canonical save model: JSON snapshot incl. site states and PRNG state; no reboot-restore/roster-number prompts. **ADR-5 [BR-7/§VI-4]** Canonical money model = constrained: treasury ≤ $65,000; credit lines ≤ $65,000. Justification: single canonical model per FR-SAV-004's principle: the constrained ceilings keep the letter-of-credit economy load-bearing to endgame (a $250 rest-house stay and the BR-11 price anchors must still mean something at high level); the pooled $10⁹ presentation survives only as the preserved packaging note in §2.5 item 4.

**ADR-6 [C-3/A-1]** Demo mode is a recorded command script played through the normal engine→frame→renderer path against a fresh seeded state — zero demo-specific code in engine or composer. Attract reel triggers from boot menu and after 60s idle [P].

**ADR-7 [§VI-6]** Roster capacity fixed at **30 slots** (27 members + 3 reserved automata) — inside the "dozens" envelope, above the 21-slot historic floor, and eliminates an unverifiable "it depends" capacity. `[P]`

**ADR-8 [R-4]** Feat-registry closure rule per §5.4 note: all quoted figures byte-preserved; quoted "1–4" labels reconciled against 56 rows by keeping Confusion at 4 tiers and binding Enervation/Paralysis to 3 rows each (labels 1/2/4); Vitriol Projector occupies the 37–40 body-area band; #53 vacant; elder rites #57/#58 per OQ-1. Every unquoted cell flagged `[P]` in the table.

**ADR-9 [D-1/OD-3]** Veteran-saga transfer removed as stale scope: FR §VII-1 stricken; FR-SES-004 retains backup/restore + erase-confirmed new game only; FR-QST Filmon greeting is single-path (*"I choose you because Doctor Voss would never suspect you."*); the resonator-shard retention rule is void with it.

**ADR-10 [D-2/OD-7]** Sound toggle ships functional and persisted (config echo honored across sessions) with **zero audio output**. Presentation packaging, not a mechanic; documented in-game as a toggle, not a promise.

---

### OQ Resolution Register — all 20 (OD-4 authority; every value `[P]`, line-item reviewable)

**OQ-1 — Elder rites.** Decision: **#57 The Calling** — MP 4, Combat domain, Active; effect only in Voss's presence (gate + Wood per FR-QST-022), otherwise "no noticeable effect at this distance" (FR-QST-021 string). **#58 Sun-Mind's Boon** — MP 4, Site domain, Active; all living members to full HP + infirmary-strength body cure (1 Broken or 2 Injured each); granted once (one praying member's slot-free rite list, BR-36). *Justification:* MP ceiling of the documented 1–4 cost band; effect modeled on the only other full-rest event in the system (FR-TWN-004) so the shrine reads as an elder aid-station; "to be used in sites" honored via the Site domain.

**OQ-2 — Level cap.** Decision: **cap 20**. HP 16–20 extends each profession's level 13→15 increment (WH/Scout +10, Doctor/Pugilist/CB +8, AM +6 → e.g., WH 180,190,200,210,220). MP frozen at level-15 values. No new feat-availability groups past 15 (documentary horizon); 3 skill trainings/level continue. *Justification:* the Hollowed-set-20 rule and the "out of a possible 20" report outrank a chart's print horizon; extrapolation is the smallest possible monotone extension.

**OQ-3 — XP thresholds.** Decision: cost to advance n→n+1 = **500 × n × S × P × A**, rounded down. S (strain): Club Stock/Scrub-Folk 1.0; Crag/Mesa-Folk 1.1; Lake-Folk 1.2; all strange strains 1.2. P (profession): WH/Scout 1.0; Pugilist/CB 0.9; Doctor 1.1; AM 1.3. A (attributes at creation): clamp(1.5 − (attrSum − 30)/100, 0.6, 1.5). *Justification:* satisfies BR-4's documented triple dependence with auditable arithmetic; level 19→20 base 9,500 × factors ≈ 7k–17k XP — reachable inside the BR-12 per-kill ceiling's economy.

**OQ-4 — Cost curves.** Decision: training to level L = **200 × L × ((21 − CHA)/10) × (1 + 0.05 × trainings_taken_lifetime)**, floored to whole dollars. Feat-learn attempt = **150 × feat_MP_cost × ((21 − CHA)/10)**. *Justification:* CHA-linked per the documented rule; mid-curve stays affordable (CHA 11, L8, 24 trainings ≈ $3,520); the extreme tail reproduces the source's anecdotal case exactly (L15, CHA 3, 45 trainings = $17,550 — the "$15,000 exaggeration" is real at the margin, priced out of normal play).

**OQ-5 — Feat-availability matrix.** Decision (rule; full 6×15 matrix generated into Doc 2 §5R-4b): each profession owns an **ordered unlock list** by theme (AM: device/mesmerism breadth — anchor row L1 = {#5 Thermal Lancet 1, #13 Incendiary Loads 1} preserved verbatim; Doctor: Sutures → Counter-Talisman → Awaken control line; Scout: Field Assessment/Recall/adrenal utility; Pugilist: Trances + Adrenal Surge early; CB: Charm/Egress/Confusion trickery; WH: narrow — Surge/Hardening/Lancet). Level k offers that profession's next list entries. Learnable slots (BR-6) = **profRate × level + max(0, INT − 10)**, profRate: AM 2, Doctor 2, Scout 1, Pugilist 1, WH 1, CB 1. *Justification:* profession identity maps to feat families; INT gate matches the documented "profession/level/Intelligence" triple.

**OQ-6 — Aging.** Decision (calendar): trail/badlands move = 1 day; swamp = 2; escarpment = 3; river +1; site time = 1 day per 10 moves (min 1/leg); infirmary/rest-house stay = 7 days; camp night = 1 day; 30-day months, 360-day years. Decline at 50%/70%/90% of strain lifespan: STR/DEX/CON −1/−2/−3 cumulative; INT/CHA −1 at 90% only. *Justification:* a 75-square cross-province trek = 75–150 days ≈ the documented "~2 months" retrieval report; thresholds preserve the RS-3 longevity fiction (Club Stock declines ~40yr, Lake-Folk ~1500yr).

**OQ-7 — Infamy.** Decision: logged acts — **smashed crystal statue +1** (three available, D6); **destroyed Map Room shrine +2**; nothing else logs (corridor kills of friendly settlements never count; `[REQ]` note honored). Tiers: 0 pure / 1–2 stained / **≥3 blackened** (three statues suffice = the documented "completely infamous" report). Gates: pure → Drowned gate "not infamous enough", key required; stained → doubtful wording, still barred, key required; blackened → "Enter, infamous ones" (no key needed). Voss talk tiers per FR-QST-022 strings. **Wood's camp: empty at any infamy ≥ 1** — resolution of a sealed-source wording split in favor of the canonical FR text ("Lord Wood withdraws if the expedition has turned infamous," §II/FR-QST-019) over the companion's "blackened" phrasing [OD-1 hierarchy].

**OQ-8 — Menace repertoires.** Decision: per §5.6 rule — each caster type = one offense line (tier→Lancet/Sweep/Assault) + one control (Sleep/Dread/Enervation), casts/combat = 2/3/4/5 by tier, 50% cast-instead-of-melee chance; enemy mesmerist feat-countering implemented as: enemy cast cancels one active column Passive feat (BR-37 inverse). Per-caster assignments table → Doc 2 §5R-6.

**OQ-9 — Credit shares.** Decision: **Urchin 1 / Stoker 2 / Artisan 2 / Patrician 3**. *Justification:* lineage INFERRED ties shares to standing; monotonic within four standings; rounding-down behavior (BR-7 exemplar) unchanged.

**OQ-10 — Hermit's broth.** Decision: each bowl = **+1 to the chosen attribute for every present member**; both bowls same attribute per sitting ("all must take the same brew"); second bowl deferrable; total 2 bowls ever, once-ever flag (BR-36); cannot exceed strain maximum (BR-3). *Justification:* reproduces the reported "+2 total, once-only" contract.

**OQ-11 — Tribunal.** Decision: judgement **on total expedition death only**; Hollowed **irreversible**; per-member P(returned) = **clamp(0.5 + (Luck − 10)×0.02 + questScore×0.002, 0.10, 0.90)**. Returned: carried dollars lost, CON −1 (BR-31). *Justification:* defaults honored ("wipe-only, irreversible"); formula uses documented inputs (Luck, quest progress) so veterans of the spine judged kinder; floor/ceiling keeps both outcomes alive.

**OQ-12 — Folio XVI.** Decision: **mark unused**, executed as an item — "Sealed Folio: water-ruined, illegible" (valuables table; readable attempt → "The ink has long since run to ruin."). Zero new lore authored.

**OQ-13 — #53.** Decision: vacant/unlearnable (recommendation honored; the "Aerial Survey unnecessary — province pre-mapped" handbook joke preserved as a folio margin note string).

**OQ-14 — Rest-house anomaly.** Decision: **Royal Rest** canonical (recommendation honored); list per §2.4 R-7: Deadfall Rest, Crown Rest, Portage House, Mirage Rest, Badlands Rest, Campfire Rest, Royal Rest, Jolly Rest.

**OQ-15 — Starter six.** Decision: pre-generated expedition ships on all builds (recommendation honored; FR-CHR-002).

**OQ-16 — Quirk quarantine.** Decision: **fix silently** (recommendation honored): (a) beast-lever edge — a slain beast is never declared a pit winner; (b) sites ship as separate 30×24 grids (merged-map port anomaly rejected); (c) archival misprints corrected in all strings; (d) the HP-0 fauna record (hyena) corrected to its tier value; (e) duplicate Folio III/VII item instances deduplicated to single identities; (f) wrestling pit = **once per party**, flagged.

**OQ-17 — Counter-Talisman cost.** Decision: **MP 1** (suggestion honored; R-4 row 49).

**OQ-18 — Ending rewards.** Decision: both endings — treasury **+$20,000** (overflow per BR-7 cap is forfeited, message shown) and **+50,000 XP each surviving member** (award, not kill — inside BR-12's ceiling regardless). Good ending: +1 elder-work melee weapon per living member drawn from the value 20–25 master-/sun-metal band. Evil ending: +1 **Obsidian Regalia** armor piece (value 11, elder-work prereq discount) per living member; the Obsidian Urn's shards become a curio. World stays static; play continues (FR-QST-023). *Justification:* honors "equipment and experience" qualitatively while sizing to the late-game ledger; no new systems introduced.

**OQ-19 — Rates & surrender.** Decision: wilderness per-move menace chance — game trail 1/12, badlands 1/10, swamp 1/8, escarpment 1/6, rivers 0 `[REQ: no encounters in water]`; night camp every 10th trail move: ambush 1/3, sentry Listen decides Sleeping start; sites 1/12 per move plus scripted squares; **surrender threshold: ≥ 50% of pack killed**. *Justification:* supports §VI-7's tier-scaled, grind-mitigated pacing; 50% reads "depleted" per FR-ENC-003.

**OQ-20 — Starting skills & credit.** Decision (skills Attack/Parry/Swim/Listen/Spot/Disarm/Find/Pick/Marksman):

| Profession | Atk | Pary | Swim | List | Spot | Disarm | Find | Lock | Mrks |
|---|---|---|---|---|---|---|---|---|---|
| White Hunter | 50 | 30 | 25 | 20 | 10 | 5 | 15 | 5 | 25 |
| Pugilist | 45 | 35 | 20 | 15 | 5 | 5 | 10 | 5 | 10 |
| Expedition Doctor | 25 | 15 | 20 | 25 | 15 | 10 | 20 | 10 | 15 |
| Scout | 40 | 25 | 35 | 35 | 25 | 20 | 30 | 15 | 30 |
| Cat Burglar | 35 | 25 | 20 | 30 | 35 | 40 | 35 | 45 | 45* |
| Antiquarian-Mesmerist | 20 | 10 | 15 | 25 | 20 | 15 | 25 | 15 | 15 |

\*CB Marksman = 15 + 30 anchor `[REQ FR-ADV-002]` baked in. Strain adds: Lake-Folk +15 Marksman `[REQ anchor]`; Crag-Folk +5 Parry; Mesa-Folk +5 Marksman (bowyer culture fiction, C-8-legal); Scrub-Folk +5 Spot/+5 Disarm; others +0. Credit line: **Urchin $250 / Stoker $500 / Artisan $1,000 / Patrician $2,500**; level-up award = 100 × new level × standing-shares. *Justification:* profession silhouette read at a glance; an Urchin's $250 equals exactly one rest-house fee (BR-11 anchor).

---

## 11. Open Questions & Assumptions

**Open questions for the operator: none beyond line-item `[P]` review.** The sealed register's twenty quarantines are resolved above; twelve closed reskin decisions (RS-1…RS-12) are honored as encoded in §§2–6 and need no further ruling: RS-1 single Fire ladder/no ammo economy; RS-2 modern-care framing (C-9); RS-3 longevity handwave; RS-4 dollars; RS-5 post-only folio reading; RS-6 mummified/Hollowed flag rename; RS-7 Sun-Mind/Drowned-Mind ending voices; RS-8 psychic-duel set-piece text preserved; RS-9 infamy track rename; RS-10 "Old Chronos" proper name retained; RS-11 starter-six composition; RS-12 elder-work/master-work naming with prereq discount.

**Assumptions in force (interview record; correct at review if wrong):** A-1 demo reel in scope as script playback [ADR-6]; A-2 every FR-ID an acceptance-test anchor, both endings headlessly completable; A-3 unquoted registry cells authored under OD-4 as `[P]`; A-4 PyInstaller-class packaging late in build order.

**Notes:** (1) BR-14…BR-29 carry no entries in the sealed register; numbering is preserved and absent numbers are non-requirements, not omissions. (2) The data-generation rule binding Doc 2 §5: rows must be `[REQ]`, `[OD]`, `[P]`, or mechanically implied by one — no Doc-2-only inventions; enforced by the §16 consistency checklist. (3) Folio payload mapping: canon numbering/locations (R-5) prevail; companion texts are re-authored to canonical nouns by **lore-topic match**, not by its numbering [OD-1]; the topic-match table ships in Doc 2 §5R-5. (4) Companion-scene enrichment transferred where noun-compatible: funeral guest rows as canonical list (§2.2 FR-QST-010), Station dossier shelves (Ages of Light…present age), drake purring strings, color-text registry (port-and-cheese, waste-paper pit, weapon cupboard, "Avoid the Titan living-quarters…"→*"Avoid the Colossi pens until you are strong enough"*, *"Light is opposed by darkness"*→*"The Sun-Mind is opposed by the Drowned Mind"*, *"Have courage, mighty travelers"*, hideous laugh, lifeless chill, scorched bones/empty chairs) — all as strings per C-8/C-9.

**Carried risks:** R-1 `[P]` balance divergence (mitigated by anchors + review); R-2 cross-doc inconsistency (Doc 2 §§15–16 gates); R-3 content volume (Doc 3 sequencing); R-4 funeral/Tribunal/infamy cross-save interactions (dedicated trace cases).

---
