<!-- Version: 0.1.0 | 2026-11-02 -->
# Implementation status

## Phase 0

WP-0.1: project metadata, Python/tcod constraints, development and release
extras, declared console scripts, package directories, and packaging stub exist.
Future module files are intentionally deferred to their owning work packages;
Phase 0 creates package initializers only, as required by WP-0.1.

WP-0.2: isolated CRADLE_HOME/save directory fixtures, explicit seed fixtures,
fixture documentation, and the six verbatim C-8 blocklist terms exist.

Validation completed in a clean Python 3.12.14 virtual environment:
`pip install -e ".[dev]"` succeeded; all 17 pytest cases passed; `pip check`
reported no broken requirements; `git diff --check` passed. Scaffold checks
verify installed metadata, package imports, fixture isolation, the blocklist,
and engine import direction. Game state is not constructed by any fixture.

## Open specification issue: C-9 blocklist

WP-0.2 requires a period-rhetoric list. Doc 1 C-9 defines the framing policy but
supplies no lexemes; Doc 2 §5.0 refers to tests/fixtures/lint_blocklist.txt as the
source of the exact list, which did not exist. Per roadmap §0, no additional
terms have been invented. The fixture contains only the six explicit C-8 terms.
WP-0.2 remains incomplete for C-9 until the authoritative list is supplied.
Full C-9 lint acceptance must not be claimed in later phases until resolved.
