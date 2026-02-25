# ABOUTME: Tests for lifecycle costing calculations per BS15663 Part 2 (2001) and
# ABOUTME: marine transportation cost modelling per O&G 0030-4.

import math
import pytest

from assetutilities.calculations.lifecycle_cost import (
    net_present_value,
    levelized_cost,
    annual_equivalent_cost,
    maintenance_cost_mtbf,
    marine_transport_cost,
    effective_transit_days,
    total_installed_cost,
)


# ---------------------------------------------------------------------------
# net_present_value
# ---------------------------------------------------------------------------
class TestNetPresentValue:
    def test_zero_discount_rate_sums_all_costs(self):
        costs = [1000.0, 1000.0, 1000.0]
        result = net_present_value(costs, discount_rate=0.0)
        assert result == pytest.approx(3000.0, rel=1e-9)

    def test_single_cost_at_year_zero_not_discounted(self):
        costs = [5000.0]
        result = net_present_value(costs, discount_rate=0.10)
        assert result == pytest.approx(5000.0, rel=1e-9)

    def test_single_cost_at_year_one_discounted(self):
        costs = [0.0, 1100.0]
        result = net_present_value(costs, discount_rate=0.10)
        # Year 0 = 0, year 1 = 1100 / 1.10 = 1000
        assert result == pytest.approx(1000.0, rel=1e-6)

    def test_two_year_example_known_result(self):
        # NPV = 1000 / 1.0 + 1100 / 1.1^1 = 1000 + 1000 = 2000
        costs = [1000.0, 1100.0]
        result = net_present_value(costs, discount_rate=0.10)
        assert result == pytest.approx(2000.0, rel=1e-6)

    def test_higher_discount_rate_lowers_npv(self):
        costs = [1000.0] * 10
        npv_low = net_present_value(costs, discount_rate=0.05)
        npv_high = net_present_value(costs, discount_rate=0.15)
        assert npv_high < npv_low

    def test_empty_cost_list_returns_zero(self):
        result = net_present_value([], discount_rate=0.10)
        assert result == pytest.approx(0.0)

    def test_five_year_uniform_cost_spot_check(self):
        # 1000 per year for 5 years at 8%
        costs = [1000.0] * 5
        result = net_present_value(costs, discount_rate=0.08)
        expected = sum(1000.0 / (1.08 ** t) for t in range(5))
        assert result == pytest.approx(expected, rel=1e-9)

    def test_result_is_positive_for_positive_costs(self):
        costs = [500.0, 600.0, 700.0]
        result = net_present_value(costs, discount_rate=0.05)
        assert result > 0.0


# ---------------------------------------------------------------------------
# levelized_cost
# ---------------------------------------------------------------------------
class TestLevelizedCost:
    def test_uniform_costs_and_output_returns_cost_per_unit(self):
        # Equal costs and output, zero discount => LCOE = cost/output = 1.0
        costs = [100.0, 100.0, 100.0]
        outputs = [100.0, 100.0, 100.0]
        result = levelized_cost(costs, outputs, discount_rate=0.0)
        assert result == pytest.approx(1.0, rel=1e-9)

    def test_lcoe_scales_with_cost_magnitude(self):
        costs_high = [200.0, 200.0]
        costs_low = [100.0, 100.0]
        outputs = [100.0, 100.0]
        lcoe_high = levelized_cost(costs_high, outputs, discount_rate=0.05)
        lcoe_low = levelized_cost(costs_low, outputs, discount_rate=0.05)
        assert lcoe_high == pytest.approx(2.0 * lcoe_low, rel=1e-6)

    def test_higher_discount_rate_raises_lcoe_when_costs_are_front_loaded(self):
        # Capital-intensive project: large upfront cost, growing output over time.
        # Higher discount rate penalises the distant output more than the near cost,
        # so LCOE rises with discount rate.
        costs = [5000.0, 100.0, 100.0, 100.0, 100.0]
        outputs = [10.0, 200.0, 400.0, 600.0, 800.0]
        lcoe_low = levelized_cost(costs, outputs, discount_rate=0.02)
        lcoe_high = levelized_cost(costs, outputs, discount_rate=0.20)
        assert lcoe_high > lcoe_low

    def test_known_two_period_manual_check(self):
        # costs=[100, 110], outputs=[50, 55], r=0.10
        # disc_costs  = 100/1 + 110/1.1 = 100 + 100 = 200
        # disc_output = 50/1  +  55/1.1 =  50 +  50 = 100
        # LCOE = 200/100 = 2.0
        costs = [100.0, 110.0]
        outputs = [50.0, 55.0]
        result = levelized_cost(costs, outputs, discount_rate=0.10)
        assert result == pytest.approx(2.0, rel=1e-6)

    def test_result_positive_for_positive_inputs(self):
        result = levelized_cost([500.0, 500.0], [250.0, 250.0], discount_rate=0.05)
        assert result > 0.0


# ---------------------------------------------------------------------------
# annual_equivalent_cost
# ---------------------------------------------------------------------------
class TestAnnualEquivalentCost:
    def test_aec_times_annuity_factor_equals_npv(self):
        npv = 10_000.0
        r = 0.08
        n = 10
        aec = annual_equivalent_cost(npv=npv, discount_rate=r, life_years=n)
        # AEC * annuity_pv_factor should recover npv
        annuity_pv = (1.0 - (1.0 + r) ** (-n)) / r
        assert aec * annuity_pv == pytest.approx(npv, rel=1e-6)

    def test_higher_npv_gives_higher_aec(self):
        r, n = 0.08, 20
        aec_low = annual_equivalent_cost(npv=5_000.0, discount_rate=r, life_years=n)
        aec_high = annual_equivalent_cost(npv=10_000.0, discount_rate=r, life_years=n)
        assert aec_high > aec_low

    def test_longer_life_gives_lower_aec(self):
        npv, r = 50_000.0, 0.06
        aec_short = annual_equivalent_cost(npv=npv, discount_rate=r, life_years=5)
        aec_long = annual_equivalent_cost(npv=npv, discount_rate=r, life_years=25)
        assert aec_long < aec_short

    def test_manual_check_known_values(self):
        # AEC = NPV * r / (1 - (1+r)^(-n))
        # NPV=1000, r=0.10, n=5
        # AEC = 1000 * 0.10 / (1 - 1.1^-5) = 100 / (1 - 0.6209) = 100 / 0.3791 ≈ 263.8
        npv, r, n = 1000.0, 0.10, 5
        expected = npv * r / (1.0 - (1.0 + r) ** (-n))
        result = annual_equivalent_cost(npv=npv, discount_rate=r, life_years=n)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_result_is_positive(self):
        result = annual_equivalent_cost(npv=20_000.0, discount_rate=0.07, life_years=15)
        assert result > 0.0


# ---------------------------------------------------------------------------
# maintenance_cost_mtbf
# ---------------------------------------------------------------------------
class TestMaintenanceCostMtbf:
    def test_one_year_one_failure_per_year(self):
        # MTBF = 1 year, cost_per_event = 500, years = 1 => 500
        result = maintenance_cost_mtbf(
            cost_per_event=500.0, mtbf_years=1.0, years=1.0
        )
        assert result == pytest.approx(500.0, rel=1e-9)

    def test_proportional_to_years(self):
        c1 = maintenance_cost_mtbf(cost_per_event=200.0, mtbf_years=2.0, years=5.0)
        c2 = maintenance_cost_mtbf(cost_per_event=200.0, mtbf_years=2.0, years=10.0)
        assert c2 == pytest.approx(2.0 * c1, rel=1e-9)

    def test_proportional_to_cost_per_event(self):
        c1 = maintenance_cost_mtbf(cost_per_event=100.0, mtbf_years=4.0, years=8.0)
        c2 = maintenance_cost_mtbf(cost_per_event=300.0, mtbf_years=4.0, years=8.0)
        assert c2 == pytest.approx(3.0 * c1, rel=1e-9)

    def test_longer_mtbf_lower_cost(self):
        c_short = maintenance_cost_mtbf(cost_per_event=1000.0, mtbf_years=1.0, years=20.0)
        c_long = maintenance_cost_mtbf(cost_per_event=1000.0, mtbf_years=5.0, years=20.0)
        assert c_long < c_short

    def test_formula_manual_check(self):
        # expected = cost_per_event / mtbf * years = 250 / 2.5 * 10 = 1000
        result = maintenance_cost_mtbf(cost_per_event=250.0, mtbf_years=2.5, years=10.0)
        assert result == pytest.approx(1000.0, rel=1e-9)


# ---------------------------------------------------------------------------
# marine_transport_cost
# ---------------------------------------------------------------------------
class TestMarineTransportCost:
    def test_zero_day_rate_no_transit_cost(self):
        result = marine_transport_cost(
            mobilization=5000.0,
            transit_day_rate=0.0,
            transit_days=10.0,
            demobilization=3000.0,
        )
        assert result == pytest.approx(8000.0, rel=1e-9)

    def test_components_sum_correctly(self):
        mob = 10_000.0
        rate = 2_000.0
        days = 7.0
        demob = 8_000.0
        result = marine_transport_cost(mob, rate, days, demob)
        expected = mob + rate * days + demob
        assert result == pytest.approx(expected, rel=1e-9)

    def test_longer_transit_increases_cost(self):
        cost_short = marine_transport_cost(5000.0, 1500.0, 3.0, 5000.0)
        cost_long = marine_transport_cost(5000.0, 1500.0, 10.0, 5000.0)
        assert cost_long > cost_short

    def test_higher_day_rate_increases_cost(self):
        cost_low = marine_transport_cost(5000.0, 1000.0, 5.0, 5000.0)
        cost_high = marine_transport_cost(5000.0, 3000.0, 5.0, 5000.0)
        assert cost_high > cost_low

    def test_all_zero_returns_zero(self):
        result = marine_transport_cost(0.0, 0.0, 0.0, 0.0)
        assert result == pytest.approx(0.0)

    def test_result_is_positive_for_positive_inputs(self):
        result = marine_transport_cost(8000.0, 2500.0, 5.0, 6000.0)
        assert result > 0.0


# ---------------------------------------------------------------------------
# effective_transit_days
# ---------------------------------------------------------------------------
class TestEffectiveTransitDays:
    def test_zero_downtime_returns_nominal_days(self):
        result = effective_transit_days(nominal_days=10.0, downtime_fraction=0.0)
        assert result == pytest.approx(10.0, rel=1e-9)

    def test_fifty_percent_downtime_doubles_days(self):
        result = effective_transit_days(nominal_days=10.0, downtime_fraction=0.5)
        assert result == pytest.approx(20.0, rel=1e-6)

    def test_twenty_percent_downtime_manual_check(self):
        # effective = 10 / (1 - 0.20) = 10 / 0.80 = 12.5
        result = effective_transit_days(nominal_days=10.0, downtime_fraction=0.20)
        assert result == pytest.approx(12.5, rel=1e-9)

    def test_effective_always_gte_nominal(self):
        for fraction in [0.0, 0.1, 0.25, 0.5]:
            result = effective_transit_days(nominal_days=8.0, downtime_fraction=fraction)
            assert result >= 8.0

    def test_downtime_fraction_near_one_raises_value_error(self):
        with pytest.raises(ValueError):
            effective_transit_days(nominal_days=5.0, downtime_fraction=1.0)

    def test_negative_downtime_raises_value_error(self):
        with pytest.raises(ValueError):
            effective_transit_days(nominal_days=5.0, downtime_fraction=-0.1)


# ---------------------------------------------------------------------------
# total_installed_cost
# ---------------------------------------------------------------------------
class TestTotalInstalledCost:
    def test_all_components_sum_correctly(self):
        result = total_installed_cost(
            equipment=100_000.0,
            transport=20_000.0,
            installation=30_000.0,
            commissioning=5_000.0,
            contingency=15_500.0,
        )
        assert result == pytest.approx(170_500.0, rel=1e-9)

    def test_zero_contingency_still_works(self):
        result = total_installed_cost(
            equipment=50_000.0,
            transport=10_000.0,
            installation=15_000.0,
            commissioning=2_000.0,
            contingency=0.0,
        )
        assert result == pytest.approx(77_000.0, rel=1e-9)

    def test_result_greater_than_equipment_alone(self):
        result = total_installed_cost(
            equipment=40_000.0,
            transport=5_000.0,
            installation=8_000.0,
            commissioning=1_000.0,
            contingency=3_000.0,
        )
        assert result > 40_000.0

    def test_scaling_all_components_scales_tic(self):
        tic1 = total_installed_cost(10_000.0, 2_000.0, 3_000.0, 500.0, 1_000.0)
        tic2 = total_installed_cost(20_000.0, 4_000.0, 6_000.0, 1_000.0, 2_000.0)
        assert tic2 == pytest.approx(2.0 * tic1, rel=1e-9)

    def test_all_zero_returns_zero(self):
        result = total_installed_cost(0.0, 0.0, 0.0, 0.0, 0.0)
        assert result == pytest.approx(0.0)
