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

class TestLifecycleCost:
    def test_net_present_value_happy_path(self):
        result = net_present_value(costs=[100.0, 110.0, 121.0], discount_rate=0.1)
        assert result == pytest.approx(300.0)

    def test_net_present_value_empty_list_returns_zero(self):
        result = net_present_value(costs=[], discount_rate=0.1)
        assert result == 0.0

    def test_levelized_cost_happy_path(self):
        result = levelized_cost(costs=[100.0, 110.0], outputs=[10.0, 11.0], discount_rate=0.1)
        assert result == pytest.approx(10.0)

    def test_levelized_cost_zero_output_raises_error(self):
        with pytest.raises(ZeroDivisionError):
            levelized_cost(costs=[100.0, 110.0], outputs=[0.0, 0.0], discount_rate=0.1)

    def test_annual_equivalent_cost_happy_path(self):
        result = annual_equivalent_cost(npv=1000.0, discount_rate=0.1, life_years=10)
        assert result == pytest.approx(162.745, rel=1e-3)

    def test_annual_equivalent_cost_zero_discount_raises_error(self):
        with pytest.raises(ZeroDivisionError):
            annual_equivalent_cost(npv=1000.0, discount_rate=0.0, life_years=10)

    def test_maintenance_cost_mtbf_happy_path(self):
        result = maintenance_cost_mtbf(cost_per_event=5000.0, mtbf_years=5.0, years=20.0)
        assert result == 20000.0

    def test_marine_transport_cost_happy_path(self):
        result = marine_transport_cost(mobilization=10000.0, transit_day_rate=5000.0, transit_days=10.0, demobilization=5000.0)
        assert result == 65000.0

    def test_effective_transit_days_happy_path(self):
        result = effective_transit_days(nominal_days=10.0, downtime_fraction=0.2)
        assert result == 12.5

    def test_effective_transit_days_invalid_fraction_raises_error(self):
        with pytest.raises(ValueError, match="must be in \\[0, 1\\)"):
            effective_transit_days(nominal_days=10.0, downtime_fraction=1.0)

    def test_total_installed_cost_happy_path(self):
        result = total_installed_cost(equipment=1000.0, transport=200.0, installation=300.0, commissioning=100.0, contingency=50.0)
        assert result == 1650.0
