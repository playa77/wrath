<!-- Version: 0.1.0 | 2026-11-02 -->
# The Cradle Plateau: The Wrath of Doctor Voss

A deterministic, single-player desktop expedition game, implemented in the
phases defined in [the roadmap](docs/roadmap.md). The design and technical
specification in `docs/` are the implementation authority.

## Development

Use Python 3.12.x:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
```

Runtime dependencies are limited to `tcod>=16,<17` and the Python standard
library. The `release` extra supplies PyInstaller for Phase 8.

The `src/cradle/` tree separates engine, content, UI, renderer, and platform
infrastructure. Content JSON will be installed as package data.

## Current status

Phase 0 scaffolding and test infrastructure are in place. The console scripts
`cradle` and `cradle-content-check` are registered in package metadata; their
implementations arrive in Phases 6 and 1 respectively. They are not runnable yet.
The packaging spec is the explicitly scheduled Phase 0 stub.

See [implementation status](docs/implementation_status.md) for validation and
an upstream specification gap affecting the C-9 blocklist.
