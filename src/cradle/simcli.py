# Version: 0.2.0 | 2026-11-02
"""Headless production-command replay; no state-setting test shortcuts (C-3)."""

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from cradle.main import build_engine
from cradle.engine.state import project


def parse_script(path):
    for lineno, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), 1
    ):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            if line.startswith("{"):
                cmd = json.loads(line)
            else:
                verb, _, payload = line.partition(" ")
                cmd = dict(
                    verb=verb, actor=None, args=json.loads(payload) if payload else {}
                )
            yield lineno, cmd
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{path}:{lineno}: invalid command") from exc


def run_script(path, seed, hash_only=False):
    with TemporaryDirectory(prefix="cradle-replay-") as home:
        e, _, _ = build_engine(seed, home)
        stream = []
        for lineno, cmd in parse_script(path):
            result = e.dispatch(cmd)
            if any(x["kind"] == "ERROR" for x in result):
                raise ValueError(f"{path}:{lineno}: {result}")
            # Paths are host-specific; exclude SAVE_WRITTEN payload from canonical log.
            stream.extend(
                {**ev, "data": {} if ev["kind"] == "SAVE_WRITTEN" else ev["data"]}
                for ev in result
            )
        summary = project(e.s)
        summary["event_hash"] = hashlib.sha256(
            json.dumps(stream, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return summary, e.rng.replay_hash()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Replay Cradle commands headlessly")
    parser.add_argument("script", type=Path)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--hash", action="store_true")
    args = parser.parse_args(argv)
    try:
        summary, digest = run_script(args.script, args.seed, args.hash)
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")
    print(
        digest
        if args.hash
        else json.dumps(dict(summary=summary, replay_hash=digest), indent=2)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
