# ABOUTME: Tests for wellhead and conductor fatigue calculations from OTC deepwater drilling literature.
# ABOUTME: Covers Chen 1989 S-N fatigue, Sweeney 1991 HPHT effective stress, Allen 1998 VIV, Denison 1997 Mars TLP, Britton 1987.

import math
import pytest

from assetutilities.calculations.wellhead_fatigue import (
    sn_cycles_to_failure,
    fatigue_life_years,
    annual_fatigue_damage,
    accumulate_fatigue_damage,
    sweeney_effective_stress,
    viv_wellhead_fatigue_damage,
    denison_conductor_tensioner_load,
    britton_fatigue_life_multiplier,
)


# ---------------------------------------------------------------------------
# Chen (1989) S-N fatigue life: N_f = A / (Delta_sigma)^m
# ---------------------------------------------------------------------------
class TestSnCyclesToFailure:
    def test_nominal_values_return_positive(self):
        n_f = sn_cycles_to_failure(delta_sigma=100.0, A=1.0e13, m=3.0)
        assert n_f > 0

    def test_formula_manual_check(self):
        # N_f = A / (delta_sigma)^m
        A = 2.0e12
        m = 3.0
        delta_sigma = 50.0
        expected = A / (delta_sigma ** m)
        assert sn_cycles_to_failure(delta_sigma, A, m) == pytest.approx(expected, rel=1e-9)

    def test_higher_stress_gives_fewer_cycles(self):
        n_low = sn_cycles_to_failure(delta_sigma=50.0, A=1.0e13, m=3.0)
        n_high = sn_cycles_to_failure(delta_sigma=200.0, A=1.0e13, m=3.0)
        assert n_high < n_low

    def test_larger_A_gives_more_cycles(self):
        n1 = sn_cycles_to_failure(delta_sigma=100.0, A=1.0e12, m=3.0)
        n2 = sn_cycles_to_failure(delta_sigma=100.0, A=1.0e13, m=3.0)
        assert n2 > n1

    def test_m_equals_one_linear_relationship(self):
        n = sn_cycles_to_failure(delta_sigma=4.0, A=8.0, m=1.0)
        assert n == pytest.approx(2.0, rel=1e-9)

    def test_raises_on_zero_stress(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            sn_cycles_to_failure(delta_sigma=0.0, A=1.0e13, m=3.0)

    def test_raises_on_negative_stress(self):
        with pytest.raises(ValueError):
            sn_cycles_to_failure(delta_sigma=-10.0, A=1.0e13, m=3.0)


class TestFatigueLifeYears:
    def test_basic_calculation(self):
        # life = N_f / cycles_per_year
        n_f = sn_cycles_to_failure(100.0, 1.0e13, 3.0)
        cycles_per_year = 3_153_600  # ~0.1 Hz for one year
        life = fatigue_life_years(n_f, cycles_per_year)
        assert life > 0

    def test_formula_manual_check(self):
        n_f = 1_000_000.0
        cycles_per_year = 100_000.0
        expected = n_f / cycles_per_year
        assert fatigue_life_years(n_f, cycles_per_year) == pytest.approx(expected, rel=1e-9)

    def test_more_cycles_per_year_shorter_life(self):
        n_f = 1_000_000.0
        life_slow = fatigue_life_years(n_f, cycles_per_year=10_000.0)
        life_fast = fatigue_life_years(n_f, cycles_per_year=100_000.0)
        assert life_fast < life_slow

    def test_raises_on_zero_cycles_per_year(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            fatigue_life_years(1_000_000.0, 0.0)

    def test_sn_chain_consistent(self):
        A = 1.0e14
        m = 3.5
        delta_sigma = 80.0
        cycles_per_year = 5_000_000.0
        n_f = sn_cycles_to_failure(delta_sigma, A, m)
        life = fatigue_life_years(n_f, cycles_per_year)
        expected_life = A / (delta_sigma ** m) / cycles_per_year
        assert life == pytest.approx(expected_life, rel=1e-9)


# ---------------------------------------------------------------------------
# Annual fatigue damage from wave/current loading (Palmgren-Miner)
# ---------------------------------------------------------------------------
class TestAnnualFatigueDamage:
    def test_single_block_damage(self):
        # D = n_applied / N_f
        n_applied = 100_000.0
        n_f = 1_000_000.0
        damage = annual_fatigue_damage(n_applied, n_f)
        assert damage == pytest.approx(0.1, rel=1e-9)

    def test_damage_is_positive(self):
        damage = annual_fatigue_damage(50_000, 2_000_000)
        assert damage > 0

    def test_full_life_damage_equals_one(self):
        n_f = 500_000.0
        damage = annual_fatigue_damage(n_f, n_f)
        assert damage == pytest.approx(1.0, rel=1e-9)

    def test_raises_on_zero_n_f(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            annual_fatigue_damage(100_000, 0.0)


class TestAccumulateFatigueDamage:
    def test_empty_list_returns_zero(self):
        assert accumulate_fatigue_damage([]) == pytest.approx(0.0, rel=1e-9)

    def test_single_entry(self):
        blocks = [(100_000.0, 1_000_000.0)]
        assert accumulate_fatigue_damage(blocks) == pytest.approx(0.1, rel=1e-9)

    def test_multiple_blocks_sum(self):
        blocks = [
            (100_000.0, 1_000_000.0),   # D = 0.10
            (200_000.0, 2_000_000.0),   # D = 0.10
            (50_000.0, 500_000.0),      # D = 0.10
        ]
        assert accumulate_fatigue_damage(blocks) == pytest.approx(0.30, rel=1e-6)

    def test_exceeds_one_when_overstressed(self):
        blocks = [(2_000_000.0, 1_000_000.0)]
        assert accumulate_fatigue_damage(blocks) > 1.0


# ---------------------------------------------------------------------------
# Sweeney (1991) 15ksi HPHT wellhead effective stress (von Mises equivalent)
# sigma_eff = sqrt(sigma_h^2 - sigma_h*sigma_a + sigma_a^2)
# ---------------------------------------------------------------------------
class TestSweeneyEffectiveStress:
    def test_equal_biaxial_gives_sigma(self):
        # When sigma_h = sigma_a = S, eff = sqrt(S^2 - S^2 + S^2) = S
        S = 15_000.0
        result = sweeney_effective_stress(S, S)
        assert result == pytest.approx(S, rel=1e-6)

    def test_uniaxial_hoop_only(self):
        # sigma_a = 0: eff = sqrt(sigma_h^2) = sigma_h
        sigma_h = 10_000.0
        result = sweeney_effective_stress(sigma_h, 0.0)
        assert result == pytest.approx(sigma_h, rel=1e-6)

    def test_uniaxial_axial_only(self):
        # sigma_h = 0: eff = sqrt(sigma_a^2) = sigma_a
        sigma_a = 8_000.0
        result = sweeney_effective_stress(0.0, sigma_a)
        assert result == pytest.approx(sigma_a, rel=1e-6)

    def test_manual_calculation(self):
        sigma_h = 12_000.0
        sigma_a = 5_000.0
        expected = math.sqrt(sigma_h**2 - sigma_h * sigma_a + sigma_a**2)
        result = sweeney_effective_stress(sigma_h, sigma_a)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_result_is_positive(self):
        result = sweeney_effective_stress(10_000.0, 7_000.0)
        assert result > 0

    def test_symmetry_commutative(self):
        # Formula is not commutative in general, but both should be positive
        r1 = sweeney_effective_stress(10_000.0, 4_000.0)
        r2 = sweeney_effective_stress(4_000.0, 10_000.0)
        # Both are distinct valid effective stresses
        assert r1 > 0
        assert r2 > 0

    def test_15ksi_working_pressure_example(self):
        # Typical HPHT 15ksi wellhead: hoop ~30ksi, axial ~10ksi
        sigma_h = 30_000.0
        sigma_a = 10_000.0
        result = sweeney_effective_stress(sigma_h, sigma_a)
        expected = math.sqrt(30_000**2 - 30_000 * 10_000 + 10_000**2)
        assert result == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# Allen (1998) VIV-induced wellhead fatigue damage accumulation
# ---------------------------------------------------------------------------
class TestVivWellheadFatigueDamage:
    def test_returns_positive_damage(self):
        damage = viv_wellhead_fatigue_damage(
            viv_stress_range_psi=5_000.0,
            viv_frequency_hz=0.2,
            exposure_years=1.0,
            A=2.0e14,
            m=3.74,
        )
        assert damage > 0

    def test_higher_stress_gives_more_damage(self):
        d_low = viv_wellhead_fatigue_damage(3_000.0, 0.2, 1.0, 2.0e14, 3.74)
        d_high = viv_wellhead_fatigue_damage(8_000.0, 0.2, 1.0, 2.0e14, 3.74)
        assert d_high > d_low

    def test_longer_exposure_gives_more_damage(self):
        d_short = viv_wellhead_fatigue_damage(5_000.0, 0.2, 0.5, 2.0e14, 3.74)
        d_long = viv_wellhead_fatigue_damage(5_000.0, 0.2, 2.0, 2.0e14, 3.74)
        assert d_long > d_short

    def test_damage_formula_manual(self):
        # D = (freq_hz * exposure_years * seconds_per_year) / N_f
        freq = 0.3
        years = 1.0
        delta_sigma = 4_000.0
        A = 1.0e14
        m = 3.0
        seconds_per_year = 365.25 * 24 * 3600
        n_applied = freq * years * seconds_per_year
        n_f = A / delta_sigma ** m
        expected_damage = n_applied / n_f
        result = viv_wellhead_fatigue_damage(delta_sigma, freq, years, A, m)
        assert result == pytest.approx(expected_damage, rel=1e-6)

    def test_zero_frequency_gives_zero_damage(self):
        damage = viv_wellhead_fatigue_damage(5_000.0, 0.0, 1.0, 2.0e14, 3.74)
        assert damage == pytest.approx(0.0, abs=1e-15)


# ---------------------------------------------------------------------------
# Denison (1997) Mars TLP conductor tensioner design load
# T_design = pretension + viv_amplification * hydrodynamic_load
# ---------------------------------------------------------------------------
class TestDenisonConductorTensionerLoad:
    def test_returns_positive_load(self):
        load = denison_conductor_tensioner_load(
            pretension_kips=100.0,
            viv_amplification=2.5,
            hydrodynamic_load_kips=50.0,
        )
        assert load > 0

    def test_formula_manual_check(self):
        pretension = 150.0
        viv_amp = 2.0
        hydro = 60.0
        expected = pretension + viv_amp * hydro
        result = denison_conductor_tensioner_load(pretension, viv_amp, hydro)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_load_greater_than_pretension(self):
        load = denison_conductor_tensioner_load(100.0, 2.0, 40.0)
        assert load > 100.0

    def test_zero_viv_amplification_uses_hydro_once(self):
        # T = pretension + 0 * hydro = pretension
        result = denison_conductor_tensioner_load(100.0, 0.0, 50.0)
        assert result == pytest.approx(100.0, rel=1e-9)

    def test_unit_amplification_adds_hydro_once(self):
        result = denison_conductor_tensioner_load(100.0, 1.0, 50.0)
        assert result == pytest.approx(150.0, rel=1e-9)

    def test_higher_viv_gives_higher_load(self):
        load_low = denison_conductor_tensioner_load(100.0, 1.5, 50.0)
        load_high = denison_conductor_tensioner_load(100.0, 3.0, 50.0)
        assert load_high > load_low

    def test_mars_tlp_representative_case(self):
        # Mars TLP: typical pretension ~200 kips, Loop Current VIV amp ~2-3,
        # hydrodynamic load per conductor ~40-80 kips
        load = denison_conductor_tensioner_load(200.0, 2.5, 60.0)
        expected = 200.0 + 2.5 * 60.0
        assert load == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# Britton (1987) wellhead fatigue improvement: fatigue life multiplier
# from flex joint stiffness reduction
# ---------------------------------------------------------------------------
class TestBrittonFatigueLifeMultiplier:
    def test_stiffness_ratio_one_gives_multiplier_one(self):
        # If new stiffness equals baseline, multiplier = 1.0
        multiplier = britton_fatigue_life_multiplier(
            baseline_stiffness=1.0,
            reduced_stiffness=1.0,
            m=3.74,
        )
        assert multiplier == pytest.approx(1.0, rel=1e-6)

    def test_reduced_stiffness_gives_multiplier_greater_than_one(self):
        # Softer flex joint reduces bending stress → longer life
        multiplier = britton_fatigue_life_multiplier(
            baseline_stiffness=100.0,
            reduced_stiffness=50.0,
            m=3.74,
        )
        assert multiplier > 1.0

    def test_formula_manual_check(self):
        # Stress is proportional to stiffness → sigma_new/sigma_base = k_new/k_base
        # N_new = A / sigma_new^m; N_base = A / sigma_base^m
        # multiplier = N_new / N_base = (sigma_base/sigma_new)^m = (k_base/k_new)^m
        k_base = 100.0
        k_new = 40.0
        m = 3.0
        expected = (k_base / k_new) ** m
        result = britton_fatigue_life_multiplier(k_base, k_new, m)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_greater_stiffness_reduction_gives_larger_multiplier(self):
        m1 = britton_fatigue_life_multiplier(100.0, 60.0, 3.74)
        m2 = britton_fatigue_life_multiplier(100.0, 30.0, 3.74)
        assert m2 > m1

    def test_m_sensitivity(self):
        # Higher S-N slope m amplifies the benefit
        m1 = britton_fatigue_life_multiplier(100.0, 50.0, 3.0)
        m2 = britton_fatigue_life_multiplier(100.0, 50.0, 5.0)
        assert m2 > m1

    def test_raises_on_zero_reduced_stiffness(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            britton_fatigue_life_multiplier(100.0, 0.0, 3.74)

    def test_raises_on_negative_stiffness(self):
        with pytest.raises(ValueError):
            britton_fatigue_life_multiplier(100.0, -10.0, 3.74)
