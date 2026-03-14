"""Shared math helpers — interpolation and numerical integration."""
import math
from typing import List


def linear_interp(
    x: float,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    allow_extrapolation: bool = False,
) -> float:
    """Linear interpolation between two points."""
    if not allow_extrapolation:
        lo, hi = min(x0, x1), max(x0, x1)
        if x < lo - 1e-12 or x > hi + 1e-12:
            raise ValueError(
                f"x={x} is outside the interval [{lo}, {hi}]"
            )
    t = (x - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)


def table_interp_1d(
    x: float, xs: List[float], ys: List[float]
) -> float:
    """Piecewise-linear interpolation over a sorted table."""
    if len(xs) != len(ys):
        raise ValueError("xs and ys must have the same length")
    if len(xs) < 2:
        raise ValueError("Need at least two points")
    for i in range(len(xs) - 1):
        if xs[i + 1] < xs[i]:
            raise ValueError("xs must be sorted in ascending order")

    # Clamp to table bounds
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]

    # Find bracketing interval
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            return linear_interp(x, xs[i], ys[i], xs[i + 1], ys[i + 1])

    return ys[-1]  # pragma: no cover


def log_linear_interp(
    x: float, x0: float, y0: float, x1: float, y1: float
) -> float:
    """Log-log interpolation (linear in log-log space)."""
    if x0 <= 0 or x1 <= 0 or y0 <= 0 or y1 <= 0 or x <= 0:
        raise ValueError("All values must be positive for log interpolation")
    log_x = math.log10(x)
    log_x0 = math.log10(x0)
    log_x1 = math.log10(x1)
    log_y0 = math.log10(y0)
    log_y1 = math.log10(y1)
    log_y = linear_interp(log_x, log_x0, log_y0, log_x1, log_y1, allow_extrapolation=True)
    return 10.0 ** log_y


def trapezoidal(xs: List[float], ys: List[float]) -> float:
    """Composite trapezoidal rule for numerical integration."""
    if len(xs) != len(ys):
        raise ValueError("xs and ys must have the same length")
    if len(xs) < 2:
        raise ValueError("Need at least two points")
    total = 0.0
    for i in range(len(xs) - 1):
        dx = xs[i + 1] - xs[i]
        total += 0.5 * dx * (ys[i] + ys[i + 1])
    return total


def simpsons(xs: List[float], ys: List[float]) -> float:
    """Composite Simpson's 1/3 rule for numerical integration."""
    if len(xs) != len(ys):
        raise ValueError("xs and ys must have the same length")
    n = len(xs)
    if n < 3 or n % 2 == 0:
        raise ValueError("Need an odd number of points (even number of intervals)")
    total = 0.0
    for i in range(0, n - 2, 2):
        h = (xs[i + 2] - xs[i]) / 2.0
        total += (h / 3.0) * (ys[i] + 4.0 * ys[i + 1] + ys[i + 2])
    return total
