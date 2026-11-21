"""Synthetic arithmetic checks for the local lifecycle-cost period convention.

API source: src/assetutilities/calculations/lifecycle_cost.py, the docstrings of
net_present_value (lines 7-20), levelized_cost (lines 31-42), and
annual_equivalent_cost (lines 50-63). Sequence positions, beginning at zero,
are discount exponents; the first cost and output are undiscounted.

All numeric inputs below are synthetic choices. Expected values follow the
independent hand calculations in each test, rather than production helpers.
These checks establish arithmetic consistency, not engineering validation,
a public reference example, or NIST qualification.
"""

import pytest

from assetutilities.calculations.lifecycle_cost import (
    annual_equivalent_cost,
    levelized_cost,
    net_present_value,
)


def test_mixed_sign_costs_follow_zero_based_discounting():
    """At r=0.1, [-100, 110, -121] discounts to [-100, 100, -100].

    Hand calculation: -100 + 110/1.1 - 121/1.21 = -100.
    """
    costs = [-100, 110, -121]
    original_costs = costs.copy()

    for values in (costs, tuple(costs)):
        assert net_present_value(values, 0.1) == pytest.approx(-100)
        assert costs == original_costs


def test_levelized_mixed_sign_costs_use_discounted_outputs():
    """Hand discounting at r=0.1 gives costs [-100, 100, -100], sum -100.

    Outputs [2, 2.2, 2.42] discount to [2, 2, 2], sum 6:
    2 + 2.2/1.1 + 2.42/1.21 = 6. The ratio is -100/6 = -50/3.
    """
    result = levelized_cost([-100, 110, -121], [2, 2.2, 2.42], 0.1)

    assert result == pytest.approx(-100 / 6)


def test_annual_equivalent_matches_independent_end_year_payments():
    """Hand calculation: [100, 121] at r=0.1 has present total 100+110=210.

    For life 2, the factor is 0.1/(1-1/1.1**2), giving annual cost 121.
    Payments occur at years 1 and 2: 121/1.1 + 121/1.21 = 110+100 = 210.
    """
    costs = [100, 121]
    present_total = costs[0] + costs[1] / 1.1
    assert present_total == pytest.approx(210)

    annual_cost = annual_equivalent_cost(present_total, 0.1, 2)
    assert annual_cost == pytest.approx(121)

    payment_present_total = annual_cost / 1.1 + annual_cost / 1.21
    assert payment_present_total == pytest.approx(210)
