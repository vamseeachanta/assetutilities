"""Calculate layback labels and tension, angle and bend-radius extrema."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class LaybackSummaryInputs:
    """Workbook units: m, degrees and Te (workbook notation); blanks are None.

    No unit conversion is performed. Supply every series in these units at
    the boundary. The workbook does not define a Te-to-force conversion.
    Series may include blanks, as Excel range extrema ignore them.
    """

    layback_distances_m: Tuple[Optional[float], ...]
    exit_tension_max_te: Tuple[Optional[float], ...]
    departure_angle_max_deg: Tuple[Optional[float], ...]
    bottom_tension_max_te: Tuple[Optional[float], ...]
    bottom_tension_min_te: Tuple[Optional[float], ...]
    minimum_bend_radius_m: Tuple[Optional[float], ...]
    allowable_curve_radius_m: Tuple[Optional[float], ...]


@dataclass(frozen=True)
class LaybackSummary:
    """Extrema retain the units of the corresponding inputs."""

    labels: Tuple[str, ...]
    exit_tension_max_te: float
    departure_angle_max_deg: float
    bottom_tension_max_te: float
    bottom_tension_min_te: float
    minimum_bend_radius_m: float
    allowable_curve_radius_max_m: float


def calculate_layback_summary(inputs: LaybackSummaryInputs) -> LaybackSummary:
    """Reproduce the labels and range extrema in the source workbook.

    Source: tests/modules/excel_utilities/custom_calculation_polynomial.xlsx,
    Sheet1. No standard or clause is cited in the workbook. Excel MAX/MIN over
    an entirely blank range returns zero; concatenating a blank adds no text.
    The workbook contains no polynomial equation to evaluate.
    """
    def extreme(values: Tuple[Optional[float], ...], minimum: bool = False) -> float:
        numbers = tuple(value for value in values if value is not None)
        return (min(numbers) if minimum else max(numbers)) if numbers else 0.0

    labels = tuple(
        "Layback distance of " + ("" if value is None else format(value, ".15g")) + " m"
        for value in inputs.layback_distances_m
    )
    return LaybackSummary(
        labels,
        extreme(inputs.exit_tension_max_te),
        extreme(inputs.departure_angle_max_deg),
        extreme(inputs.bottom_tension_max_te),
        extreme(inputs.bottom_tension_min_te, minimum=True),
        extreme(inputs.minimum_bend_radius_m, minimum=True),
        extreme(inputs.allowable_curve_radius_m),
    )
