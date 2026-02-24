# ABOUTME: TDD tests for seawater property functions (density, viscosity vs T/S).
# ABOUTME: Reference values cross-checked against UNESCO 1980 / ITTC 2011 tables.

import pytest

from assetutilities.constants.seawater import (
    seawater_density,
    seawater_dynamic_viscosity,
    seawater_kinematic_viscosity,
)


# ---------------------------------------------------------------------------
# seawater_density(temperature_c, salinity_ppt)
# ---------------------------------------------------------------------------

class TestSeawaterDensity:
    """Density of seawater in kg/m³.

    Reference values from UNESCO 1980 equation of state / Fofonoff & Millard 1983.
    """

    def test_standard_conditions_approx_1025(self):
        # At 15°C, 35 ppt → API/DNV reference value ≈ 1025 kg/m³
        rho = seawater_density(temperature_c=15.0, salinity_ppt=35.0)
        assert rho == pytest.approx(1025.0, abs=1.0)

    def test_fresh_water_at_4C(self):
        # At 4°C, 0 ppt → ~1000 kg/m³
        rho = seawater_density(temperature_c=4.0, salinity_ppt=0.0)
        assert rho == pytest.approx(1000.0, abs=1.0)

    def test_cold_seawater_denser_than_warm(self):
        # Denser at lower temperature (at same salinity)
        rho_cold = seawater_density(temperature_c=4.0, salinity_ppt=35.0)
        rho_warm = seawater_density(temperature_c=25.0, salinity_ppt=35.0)
        assert rho_cold > rho_warm

    def test_saltier_water_is_denser(self):
        # At same temperature, higher salinity → higher density
        rho_low_sal = seawater_density(temperature_c=15.0, salinity_ppt=20.0)
        rho_high_sal = seawater_density(temperature_c=15.0, salinity_ppt=40.0)
        assert rho_high_sal > rho_low_sal

    def test_density_returns_float(self):
        rho = seawater_density(temperature_c=15.0, salinity_ppt=35.0)
        assert isinstance(rho, float)

    def test_density_physical_range(self):
        # Seawater density should always be in [990, 1100] kg/m³
        for t in [0.0, 10.0, 20.0, 30.0]:
            for s in [0.0, 15.0, 30.0, 40.0]:
                rho = seawater_density(temperature_c=t, salinity_ppt=s)
                assert 990.0 < rho < 1100.0, (
                    f"Density {rho} out of range at T={t}, S={s}"
                )

    def test_zero_salinity_equals_fresh_water_approx(self):
        rho = seawater_density(temperature_c=15.0, salinity_ppt=0.0)
        assert rho == pytest.approx(999.1, abs=0.5)


# ---------------------------------------------------------------------------
# seawater_dynamic_viscosity(temperature_c, salinity_ppt) → Pa·s
# ---------------------------------------------------------------------------

class TestSeawaterDynamicViscosity:
    """Dynamic viscosity of seawater in Pa·s (N·s/m²).

    Reference: ITTC 2011 recommended procedure (7.5-02-01-03).
    Fresh water at 20°C ≈ 1.002e-3 Pa·s.
    Seawater at 15°C, 35 ppt ≈ 1.188e-3 Pa·s.
    """

    def test_returns_float(self):
        mu = seawater_dynamic_viscosity(temperature_c=15.0, salinity_ppt=35.0)
        assert isinstance(mu, float)

    def test_physical_range(self):
        # Dynamic viscosity should be in [0.5e-3, 2.5e-3] Pa·s for
        # typical seawater (0-35°C, 0-40 ppt)
        for t in [0.0, 5.0, 15.0, 25.0]:
            for s in [0.0, 20.0, 35.0]:
                mu = seawater_dynamic_viscosity(temperature_c=t, salinity_ppt=s)
                assert 0.5e-3 < mu < 2.5e-3, (
                    f"Viscosity {mu} out of range at T={t}, S={s}"
                )

    def test_viscosity_decreases_with_temperature(self):
        # Warmer → lower viscosity (for both water and seawater)
        mu_cold = seawater_dynamic_viscosity(temperature_c=5.0, salinity_ppt=35.0)
        mu_warm = seawater_dynamic_viscosity(temperature_c=25.0, salinity_ppt=35.0)
        assert mu_cold > mu_warm

    def test_higher_salinity_slightly_increases_viscosity(self):
        mu_low = seawater_dynamic_viscosity(temperature_c=15.0, salinity_ppt=0.0)
        mu_high = seawater_dynamic_viscosity(temperature_c=15.0, salinity_ppt=35.0)
        assert mu_high > mu_low

    def test_standard_seawater_15c_35ppt_approx(self):
        # ITTC 2011 Table 1: ~1.188e-3 Pa·s at 15°C, 35 ppt
        mu = seawater_dynamic_viscosity(temperature_c=15.0, salinity_ppt=35.0)
        assert mu == pytest.approx(1.188e-3, rel=0.02)

    def test_fresh_water_20c_approx(self):
        # Known reference: fresh water at 20°C ≈ 1.002e-3 Pa·s
        mu = seawater_dynamic_viscosity(temperature_c=20.0, salinity_ppt=0.0)
        assert mu == pytest.approx(1.002e-3, rel=0.03)


# ---------------------------------------------------------------------------
# seawater_kinematic_viscosity(temperature_c, salinity_ppt) → m²/s
# ---------------------------------------------------------------------------

class TestSeawaterKinematicViscosity:
    """Kinematic viscosity ν = μ / ρ in m²/s."""

    def test_returns_float(self):
        nu = seawater_kinematic_viscosity(temperature_c=15.0, salinity_ppt=35.0)
        assert isinstance(nu, float)

    def test_standard_seawater_15c_35ppt_approx(self):
        # ITTC 2011: ~1.188e-3 / 1025 ≈ 1.159e-6 m²/s at 15°C, 35 ppt
        nu = seawater_kinematic_viscosity(temperature_c=15.0, salinity_ppt=35.0)
        assert nu == pytest.approx(1.159e-6, rel=0.03)

    def test_physical_range(self):
        # Kinematic viscosity range for seawater: ~0.7e-6 to 1.8e-6 m²/s
        for t in [0.0, 15.0, 30.0]:
            for s in [0.0, 35.0]:
                nu = seawater_kinematic_viscosity(temperature_c=t, salinity_ppt=s)
                assert 0.5e-6 < nu < 2.5e-6, (
                    f"Kinematic viscosity {nu} out of range at T={t}, S={s}"
                )

    def test_kinematic_viscosity_equals_dynamic_over_density(self):
        # nu = mu / rho
        from assetutilities.constants.seawater import (
            seawater_density,
            seawater_dynamic_viscosity,
        )
        t, s = 15.0, 35.0
        mu = seawater_dynamic_viscosity(temperature_c=t, salinity_ppt=s)
        rho = seawater_density(temperature_c=t, salinity_ppt=s)
        nu = seawater_kinematic_viscosity(temperature_c=t, salinity_ppt=s)
        assert nu == pytest.approx(mu / rho, rel=1e-9)
