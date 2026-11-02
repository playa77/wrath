<!-- Version: 0.2.0 | 2026-11-02 -->
# Repository working instructions

Before selecting or implementing work:

1. Inspect the working tree and preserve uncommitted user changes.
2. Fetch the configured remote. Read current remote `main`, its README/status,
   and recent commits. Do not infer project progress from a stale checkout.
3. Base new work on current remote `main`. For ongoing branches, inspect changes
   on both sides and integrate upstream work before continuing implementation.
4. Read this file and the authoritative design, specification and roadmap sections
   for the work. Check current implementation and test evidence before deciding
   what is missing. Never repeat completed phases because local files are stale.
5. Before opening/updating a PR, fetch again, inspect the diff against current
   remote `main`, resolve conflicts and run the relevant checks. Verify the PR
   state; never call a conflicting PR ready.

All randomness uses the injected SeededRng. Engine code cannot import platform,
UI or renderer modules. Content lives in versioned JSON. Tests establish playable
state only through production commands; no test-only state-setting commands.
Every test cites its FR/BR/OQ/TRACE/AC authority. Never claim unrun acceptance gates
or sign/tag a release while required checks are incomplete.

The user authorized resolving specification gaps with minimal documented
implementation decisions; record each one in docs/implementation_decisions.md.
