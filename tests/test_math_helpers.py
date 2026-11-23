"""Tests for shared math helpers — interpolation and numerical integration."""
import pytest


class TestLinearInterpolation:
    def test_basic_interpolation(self):
        from assetutilities.math_helpers import linear_interp
        # y = 2x, interpolate at x=1.5
        result = linear_interp(x=1.5, x0=1.0, y0=2.0, x1=2.0, y1=4.0)
        assert abs(result - 3.0) < 1e-10

    def test_extrapolation_raises(self):
        from assetutilities.math_helpers import linear_interp
        with pytest.raises(ValueError, match="outside"):
            linear_interp(x=3.0, x0=1.0, y0=2.0, x1=2.0, y1=4.0)

    def test_extrapolation_allowed(self):
        from assetutilities.math_helpers import linear_interp
        result = linear_interp(x=3.0, x0=1.0, y0=2.0, x1=2.0, y1=4.0, allow_extrapolation=True)
        assert abs(result - 6.0) < 1e-10


class TestTableInterpolation:
    def test_1d_table_lookup(self):
        from assetutilities.math_helpers import table_interp_1d
        xs = [0.0, 1.0, 2.0, 3.0]
        ys = [0.0, 1.0, 4.0, 9.0]
        result = table_interp_1d(x=1.5, xs=xs, ys=ys)
        assert abs(result - 2.5) < 1e-10  # linear between (1,1) and (2,4)

    def test_at_exact_point(self):
        from assetutilities.math_helpers import table_interp_1d
        xs = [0.0, 1.0, 2.0]
        ys = [0.0, 10.0, 20.0]
        assert abs(table_interp_1d(x=1.0, xs=xs, ys=ys) - 10.0) < 1e-10

    def test_unsorted_raises(self):
        from assetutilities.math_helpers import table_interp_1d
        with pytest.raises(ValueError, match="sorted"):
            table_interp_1d(x=1.0, xs=[2.0, 1.0], ys=[1.0, 2.0])


class TestLogLinearInterpolation:
    def test_log_linear(self):
        from assetutilities.math_helpers import log_linear_interp
        import math
        # S-N curve: log10(N) = log10(a) - m*log10(S)
        # At S=100, N=1e6; at S=200, N=125000
        result = log_linear_interp(x=150.0, x0=100.0, y0=1e6, x1=200.0, y1=125000.0)
        assert result > 125000 and result < 1e6


class TestTrapezoidalIntegration:
    def test_constant_function(self):
        from assetutilities.math_helpers import trapezoidal
        xs = [0.0, 1.0, 2.0, 3.0]
        ys = [5.0, 5.0, 5.0, 5.0]
        assert abs(trapezoidal(xs, ys) - 15.0) < 1e-10

    def test_linear_function(self):
        from assetutilities.math_helpers import trapezoidal
        # integral of y=x from 0 to 2 = 2.0
        xs = [0.0, 0.5, 1.0, 1.5, 2.0]
        ys = [0.0, 0.5, 1.0, 1.5, 2.0]
        assert abs(trapezoidal(xs, ys) - 2.0) < 1e-10

    def test_mismatched_lengths_raises(self):
        from assetutilities.math_helpers import trapezoidal
        with pytest.raises(ValueError):
            trapezoidal([1.0, 2.0], [1.0])


class TestSimpsonsIntegration:
    def test_quadratic(self):
        from assetutilities.math_helpers import simpsons
        # integral of y=x^2 from 0 to 2 = 8/3 ≈ 2.6667
        xs = [0.0, 0.5, 1.0, 1.5, 2.0]
        ys = [x**2 for x in xs]
        result = simpsons(xs, ys)
        assert abs(result - 8.0/3.0) < 0.01

    def test_needs_odd_points(self):
        from assetutilities.math_helpers import simpsons
        # Simpson's needs odd number of points (even number of intervals)
        with pytest.raises(ValueError, match="odd"):
            simpsons([0, 1, 2, 3], [0, 1, 4, 9])
