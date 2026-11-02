# Version: 0.2.0 | 2026-11-02
"""ADR-2 / spec §8.3: the sole randomness source and JSON-safe replay state."""

import hashlib
import random
from collections.abc import Sequence
from typing import TypedDict


class DrawRec(TypedDict):
    tick: int
    caller: str
    dist: str
    result: int


class SeededRng:
    def __init__(self, seed: int):
        if type(seed) is not int:
            raise ValueError("seed must be an integer")
        self._random = random.Random(seed)
        self.log: list[DrawRec] = []
        self.tick = 0
        self.caller = "root"

    def reseed(self, seed: int) -> None:
        if type(seed) is not int:
            raise ValueError("seed must be an integer")
        self._random.seed(seed)
        self.log = []
        self.tick = 0
        self.caller = "root"

    def _record(self, dist: str, result: int) -> int:
        self.log.append(
            {"tick": self.tick, "caller": self.caller, "dist": dist, "result": result}
        )
        return result

    def d100(self) -> int:
        return self._record("d100", self._random.randint(1, 100))

    def dice(self, n: int, d: int) -> int:
        if type(n) is not int or type(d) is not int or n < 1 or d < 1:
            raise ValueError("dice require positive integer count and sides")
        return self._record(
            f"{n}d{d}", sum(self._random.randint(1, d) for _ in range(n))
        )

    def chance(self, pct: int) -> bool:
        if type(pct) is not int or not 0 <= pct <= 100:
            raise ValueError("chance requires an integer percentage in 0..100")
        return bool(
            self._record(f"chance({pct})", int(self._random.randint(1, 100) <= pct))
        )

    def pick[T](self, seq: Sequence[T]) -> T:
        if not seq:
            raise ValueError("cannot pick from an empty sequence")
        index = self._random.randrange(len(seq))
        self._record(f"pick({len(seq)})", index)
        return seq[index]

    def checkpoint(self) -> dict:
        """Cheap internal rollback marker; previous draw rows are append-only."""
        return dict(
            random_state=self._random.getstate(),
            log=self.log,
            log_length=len(self.log),
            tick=self.tick,
            caller=self.caller,
        )

    def rollback(self, checkpoint: dict) -> None:
        self._random.setstate(checkpoint["random_state"])
        self.log = checkpoint["log"]
        del self.log[checkpoint["log_length"] :]
        self.tick = checkpoint["tick"]
        self.caller = checkpoint["caller"]

    def state(self) -> dict:
        version, internal, gauss = self._random.getstate()
        return {
            "version": version,
            "internal": list(internal),
            "gauss": gauss,
            "tick": self.tick,
            "caller": self.caller,
            "log": [row.copy() for row in self.log],
        }

    @staticmethod
    def validate_snapshot(d: dict):
        """Pure structural validation; no secondary generator is constructed."""
        try:
            if (
                not isinstance(d, dict)
                or d["version"] != 3
                or not isinstance(d["internal"], list)
                or len(d["internal"]) != 625
                or any(type(x) is not int for x in d["internal"])
                or any(not 0 <= x <= 0xFFFFFFFF for x in d["internal"][:-1])
                or not 0 <= d["internal"][-1] <= 624
                or d["gauss"] is not None
                or type(d["tick"]) is not int
                or d["tick"] < 0
                or not isinstance(d["caller"], str)
                or not isinstance(d["log"], list)
            ):
                raise ValueError("invalid RNG state")
            log = []
            for row in d["log"]:
                if (
                    not isinstance(row, dict)
                    or type(row["tick"]) is not int
                    or row["tick"] < 0
                    or not isinstance(row["caller"], str)
                    or not isinstance(row["dist"], str)
                    or type(row["result"]) is not int
                ):
                    raise ValueError("invalid RNG draw record")
                log.append(row.copy())
            random_state = (3, tuple(d["internal"]), None)
        except (KeyError, TypeError, IndexError) as exc:
            raise ValueError("invalid RNG state") from exc
        return random_state, log

    def restore(self, d: dict) -> None:
        random_state, log = self.validate_snapshot(d)
        self._random.setstate(random_state)
        self.log = log
        self.tick, self.caller = d["tick"], d["caller"]

    def replay_hash(self) -> str:
        """Spec §10: SHA-256 over concatenated decimal draw results."""
        return hashlib.sha256(
            "".join(str(row["result"]) for row in self.log).encode()
        ).hexdigest()
