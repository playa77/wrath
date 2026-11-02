# Version: 0.2.0 | 2026-11-02
"""AC-Economy; BR-7/8; OQ-4 pure formula and command-atomicity properties."""

from copy import deepcopy
import pytest
from tests.harness import Journey
from cradle.engine.credit import apportion
from cradle.engine.training import cost_curve
from cradle.engine.state import check_invariants


def test_deposit_exemplar_and_rounding(tmp_path):
    # BR-7 exemplar; pure arithmetic inputs do not fabricate gameplay state.
    j = Journey(tmp_path)
    assert apportion(6000, [1] * 6, j.e.rules["deposit_fee"]) == [999] * 6
    for amount in range(6, 2000, 37):
        lots = apportion(amount, [1, 2, 3, 1, 2, 3], 1)
        assert sum(lots) <= amount - 6
        assert amount - 6 - sum(lots) < 6


@pytest.mark.parametrize(
    "level,cha,trainings,expected", [(8, 11, 24, 3520), (15, 3, 45, 17550)]
)
def test_cost_curve_anchors(tmp_path, level, cha, trainings, expected):
    # OQ-4 explicit mid/tail examples use the same scalar function as adv.train.
    j = Journey(tmp_path)
    assert cost_curve(level, cha, trainings, j.e.rules) == expected


@pytest.mark.parametrize("seed", range(10))
def test_rejected_commands_preserve_state_and_rng(tmp_path, seed):
    # BR-7/8 / §11: invalid operations never consume a roll or partly mutate state.
    j = Journey(tmp_path, seed).muster()
    invalid = [
        ("credit.withdraw", {"member": 1, "amount": 65001}),
        ("credit.deposit", {"amount": -1}),
        ("shop.buy", {"member": 1, "item_no": 99999}),
        ("adv.learn_feat", {"member": 1, "feat_id": 53}),
        ("chr.purge", {"member": 1, "confirm": False}),
        ("session.save", {"slot": "../evil"}),
    ]
    for verb, args in invalid:
        before = deepcopy(j.e.s)
        rng = j.e.rng.state()
        assert j.do(verb, allow_error=True, **args)[0]["kind"] == "ERROR"
        assert j.e.s == before and j.e.rng.state() == rng
        check_invariants(j.e.s)


@pytest.mark.parametrize(
    "command", [None, [], {}, dict(verb="bogus", args={}, actor=None)]
)
def test_dispatch_rejects_malformed_envelopes(tmp_path, command):
    # §11 / C-3: the facade, not just validate(), rejects malformed commands.
    j = Journey(tmp_path).muster()
    before = deepcopy(j.e.s)
    rng = j.e.rng.state()
    result = j.e.dispatch(command)
    assert result[0]["kind"] == "ERROR"
    assert j.e.s == before and j.e.rng.state() == rng
