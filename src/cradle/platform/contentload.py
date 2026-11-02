# Version: 0.1.0 | 2026-11-02
"""Spec §5.0 / WP-1.5: fail-fast immutable registry loading and string lint."""
import argparse
import json
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Callable

from cradle.engine.errors import ContentError

ORDER = ("registries", "world", "scripts", "text", "presentation")
C8_BLOCKLIST = ("magic", "spell", "god", "divine", "undead", "zombie")


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(val) for key, val in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(val) for val in value)
    return value


@dataclass(frozen=True)
class Registries:
    files: Mapping[str, Mapping]

    def __getitem__(self, name: str) -> Mapping:
        return self.files[name]

    def group(self, name: str) -> Mapping:
        return MappingProxyType({path: value for path, value in self.files.items()
                                 if path.split("/")[0] == name})

    @property
    def presentation(self) -> Mapping:
        return self.group("presentation")


# Each Phase 2 WP installs its real anchor checks here, without weakening loading.
ANCHOR_CHECKS: list[Callable[[Registries], None]] = []


def validate_anchors(regs: Registries) -> None:
    for check in ANCHOR_CHECKS:
        check(regs)


def _sort_key(path: Path, root: Path) -> tuple[int, str]:
    rel = path.relative_to(root)
    group = "scripts" if rel.parts[:2] == ("world", "scripts") else rel.parts[0]
    if group not in ORDER:
        raise ContentError(rel, "header", "unknown content group")
    return ORDER.index(group), rel.as_posix()


def load_all(root: Path) -> Registries:
    if not root.is_dir():
        raise ContentError(root, "header", "content directory does not exist")
    files = sorted(root.rglob("*.json"), key=lambda p: _sort_key(p, root))
    if not files:
        raise ContentError(root, "header", "no content registries found")
    loaded = {}
    for path in files:
        rel = path.relative_to(root).as_posix()
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            raise ContentError(rel, "header", f"invalid UTF-8 JSON: {exc}") from exc
        if not isinstance(doc, dict):
            raise ContentError(rel, "header", "expected registry object")
        if not isinstance(doc.get("registry"), str) or not doc["registry"]:
            raise ContentError(rel, "header", "registry name required")
        if type(doc.get("schema_version")) is not int or doc["schema_version"] != 1:
            raise ContentError(rel, "header", "unsupported schema_version (expected 1)")
        if not isinstance(doc.get("rows"), list):
            raise ContentError(rel, "header", "rows must be a list")
        seen = set()
        for i, row in enumerate(doc["rows"]):
            if not isinstance(row, dict):
                raise ContentError(rel, i, "row must be an object")
            if "id" in row:
                ident = row["id"]
                if type(ident) not in (str, int):
                    raise ContentError(rel, i, "id must be an integer or string")
                if ident in seen:
                    raise ContentError(rel, i, f"duplicate id {ident!r}")
                seen.add(ident)
        loaded[rel] = _freeze(doc)
    regs = Registries(MappingProxyType(loaded))
    validate_anchors(regs)
    return regs


def lint_strings(regs: Registries, blocklist: tuple[str, ...] = C8_BLOCKLIST) -> None:
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(s) for s in blocklist) + r")\b", re.I)

    def visit(value, file: str, row: str) -> None:
        if isinstance(value, Mapping):
            if value.get("preserved") is True:
                return
            for key, val in value.items():
                visit(val, file, f"{row}.{key}")
        elif isinstance(value, (tuple, list)):
            for i, val in enumerate(value):
                visit(val, file, f"{row}[{i}]")
        elif isinstance(value, str) and (hit := pattern.search(value)):
            raise ContentError(file, row, f"forbidden lexeme {hit.group()!r}")

    for file, doc in regs.files.items():
        if file.split("/")[0] in {"text", "presentation"}:
            visit(doc["rows"], file, "rows")


def check_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Cradle content registries")
    parser.add_argument("root", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[1] / "content")
    args = parser.parse_args(argv)
    try:
        regs = load_all(args.root)
        lint_strings(regs)
    except ContentError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Validated {len(regs.files)} registry files; {len(ANCHOR_CHECKS)} anchor suites.")
    return 0


if __name__ == "__main__":
    raise SystemExit(check_main())
