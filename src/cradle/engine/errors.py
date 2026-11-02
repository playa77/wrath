# Version: 0.1.0 | 2026-11-02
"""Spec §11: observable domain, content, save, and development faults."""
from pathlib import Path


class DomainError(Exception):
    def __init__(self, verb: str, reason: str):
        self.verb, self.reason = verb, reason
        super().__init__(f"{verb}: {reason}")


class ContentError(Exception):
    def __init__(self, file: str | Path, row: str | int, why: str):
        self.file, self.row, self.why = str(file), row, why
        super().__init__(f"{file}: row {row}: {why}")


class SaveError(Exception):
    """Invalid or inaccessible save/backup; never partially apply a load."""


class InvariantBreach(AssertionError):
    """Development-only violation of aggregate invariants."""
