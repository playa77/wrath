<!-- Version: 0.2.0 | 2026-11-02 -->
# Implementation decisions

The user authorized resolving and documenting specification gaps on 2026-11-02.
Doc 1 remains the authority for requirements; these decisions close contradictions
and missing implementation details without discarding explicitly named content.

- D01: Preserve all 33 named sellables: 41 valuables and 182 total item identities.
  The melee ladder also contains 41 named weapons despite its 40-row label.
  The earlier 32/40/180 assertions are off by one. Audits use 33 sellables, 41 valuables, 101 combat items, 182 total items.
- D02: Feature coordinates and the explicit sector/band formula take precedence
  over illustrative sector labels. Fourteen province posts plus three planar
  posts give seventeen; eight province sites plus three planar sites give eleven.
- D03: Preserve explicit symbol IDs, including sabre-tooth 393. Map menaces by
  table order, not by adding 324 to their IDs. Blank colors inherit hide;
  the badlands foreground aliases basalt.
- D04: Author connected corridors between listed rooms and script squares.
  Sun/Drowned citadels share a mirrored maze; Fastness has a protected hidden
  panel route, and random encounters cannot invalidate that route.
- D05: Preserve all score weights (112 total), normalize floor(raw*100/112),
  and ensure the completed campaign can reach 100 by collecting every milestone.
- D06: Saves carry a lossless engine snapshot alongside the §6.4 envelope.
  Expedition treasury is authoritative; envelope treasury must agree. Post-only
  save/continue keeps the recorded post position. RNG snapshot is separate.
- D07: Cipher invitation is preserved verbatim; its actual word count determines
  cipher length, with three filler words before each decoded word. Each vase/urn/jar ledger
  variant presents the complete invitation, preserving Doc 1's singular-urn
  trigger rather than truncating its supplied quotation to 27 words.
- D08: Where creation distributions were omitted, attributes roll 3d6 plus
  profession mods, bounded to 3..strain cap; age starts at one quarter lifespan.
  Starter members use the six documented professions and include a Crag-Folk
  scout to make the canonical Enclave route available. Start kits use rung-one
  melee, shield, armor and fire; starting feat is the matrix's first entry.
- D09: C-9 lint uses explicit dehumanizing phrases rather than banning canonical
  menace dispositions or physiology. Preserved quotations retain their exemption.
- D10: Demo reads folio IV (Terminus stock), then exercises save/continue and
  movement through production commands. It reacts to encounters through the
  same command interface; no forced victory or special engine demo behavior.
- D11: Missing exact Filmon briefs and psychic-duel prose are authored to the
  normative beats, while every supplied quotation is retained verbatim.

- D12: The amended feat matrix still omits 35 and 38–40. Add 35 at AM L9,
  and 38/39/40 at Cat Burglar L10/L12/L15. Preserve all supplied offers.
- D13: Interior escarpments remain traversable at the specified three-day cost;
  the border cliff is blocked. This preserves FR-WLD-002 despite the conflicting
  blanket blocking phrase in Doc 2 trail.step.

- D14: Tribunal Hollowed members receive the level-20 HP maximum from their
  profession table with the existing CON adjustment. The level field and HP
  table must agree; retained skills/feats do not gain free training. They remain
  permanently frozen. Returned members retain their prior level and HP maximum.

- D15: Funicular Station (58,22) lies inside the crater-lake rectangle. Add a
  causeway from (55,22) to the Station so its mandatory entrance is reachable;
  the remaining lake cells stay impassable water.

- D16: Scrub-Folk lifespan follows the unmodified charter reference of 80 years;
  strange strains use 50 years, the upper end of the supplied 40–50 range.
- D17: Good-ending equipment uses the listed identities with an elder-work
  instance annotation; evil armor is labeled Obsidian Regalia without adding a
  duplicate item identity.

- D18: Item identifiers retain the explicit string identities in the content
  tables. DTOs accept those strings. Lossless snapshots use JSON-native lists
  for explored cells and positions, and a separate Automaton DTO for reserved
  infrastructure slots. Rule messages and contextual menu labels live in
  text/runtime.json, keeping authored player text outside the engine.

- D19: Missing minimum-skill thresholds for tactic fallbacks are Attack 30,
  Slash 60 and Aim 40. Post stock tiers advance in five-level bands; unspecified
  menace treasure uses the lowest treasure band. These values fill absent tables
  and live in the rules registry.
- D20: Explicit menace-row cast budgets take precedence over generic caster
  annotations. The supplied individual repertoires remain intact.
- D21: Frozen Hollowed members cannot train or grow MP through rest. Once-ever
  scripted quest rewards still apply uniformly to the expedition, as those scenes
  explicitly promise whole-column rewards.

- D22: The attract reel's save/continue commands use isolated in-memory slots.
  Completing or interrupting playback restores the player's persistence callbacks;
  neither manual saves nor autosaves can be overwritten by the idle demo.
