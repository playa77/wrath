# Version: 0.2.0 | 2026-11-02
"""TRACE-10/11/12; AC-Campaign/Determinism/Persist: command-only golden runs."""

import json
from pathlib import Path
import pytest
from cradle.simcli import run_script

GOLDEN = Path(__file__).parent / "golden"


@pytest.mark.parametrize("kind", ["good", "evil", "tribunal", "site_reset"])
def test_golden_campaign_replays_three_times(kind):
    # AC-Campaign / C-3 / §12a: no fabricated fixtures or state-setting verbs.
    expected = json.loads((GOLDEN / "hashes.json").read_text(encoding="utf-8"))[kind]
    runs = [run_script(GOLDEN / f"golden_{kind}.txt", 7) for _ in range(3)]
    assert len({digest for summary, digest in runs}) == 1
    assert len({summary["event_hash"] for summary, digest in runs}) == 1
    assert runs[0][1] == expected["rng"]
    assert runs[0][0]["event_hash"] == expected["events"]
    for summary, digest in runs:
        assert 0 <= summary["expedition"]["treasury"] <= 65000
        assert len(summary["expedition"]["found_items"]) <= 90
        if kind in ["good", "evil"]:
            assert summary["flags"]["ending_" + kind]
            assert summary["quest_score"] == 100
            assert summary["phase"] == "site"  # play continues; no terminal state
            assert summary["world"]["map_id"] == "site09"
            for flag in [
                "kilmor_found",
                "funeral_done",
                "shrine_boon",
                "rite57_held",
                "sun_key",
                "drowned_key",
                "met_priestess",
                "drowned_gate_entered",
                "wood_met",
                "hermit_done",
                "drake_apex",
                "wrestled",
                "deeps_open",
            ]:
                assert summary["flags"][flag]
            assert any(m["xp"] >= 50000 for m in summary["roster"])
        elif kind == "tribunal":
            assert summary["phase"] == "post"
            assert summary["roster"][0]["frozen"]
            assert summary["roster"][0]["level"] == 20
        else:
            assert summary["flags"]["shrine_boon"]
            assert summary["roster"][0]["rites"].count(58) == 1
            assert summary["flags"]["site01.resonator"]
