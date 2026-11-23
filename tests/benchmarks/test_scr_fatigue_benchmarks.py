"""Performance benchmarks for SCR fatigue calculations in assetutilities.

Targets keulegan_carpenter_number and soil_interaction_fatigue_factor — pure-math,
no I/O — ideal regression indicators for refactor-induced slowdowns.

Run with:
    cd assetutilities && uv run python -m pytest tests/benchmarks/ --benchmark-only -q
"""

import pytest

from assetutilities.calculations.scr_fatigue import (
    keulegan_carpenter_number,
    soil_interaction_fatigue_factor,
)

# Synthetic inputs representative of a typical SCR in 1000 m water depth
_U_M = 0.35      # m/s  — near-seabed oscillatory velocity
_PERIOD = 12.0   # s    — dominant wave period
_DIAMETER = 0.32  # m   — 12-inch OD SCR


def test_bench_keulegan_carpenter_number(benchmark):
    """Benchmark KC number computation: KC = U_m * T / D."""
    result = benchmark(keulegan_carpenter_number, _U_M, _PERIOD, _DIAMETER)
    assert result == pytest.approx(_U_M * _PERIOD / _DIAMETER, rel=1e-9)


def test_bench_soil_interaction_fatigue_factor(benchmark):
    """Benchmark soil interaction fatigue factor over KC sweep."""
    kc_values = [float(k) for k in range(1, 21)]

    def _sweep():
        return [soil_interaction_fatigue_factor(kc) for kc in kc_values]

    result = benchmark(_sweep)
    assert len(result) == 20
    assert all(f >= 1.0 for f in result)
