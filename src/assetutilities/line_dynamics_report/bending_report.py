"""Reduce line-dynamics responses into bending-report rows and extrema."""

import math
from dataclasses import dataclass
from typing import Optional, Tuple, Union


Scalar = Union[float, str]
FILENAME_VALUE_CHARACTERS = 4
REPORT_STEP_CHARACTERS = 6


@dataclass(frozen=True)
class DirectionConvention:
    """Angle defaults are formula literals; their convention is not cited."""

    full_turn_deg: float = 360.0
    north_offset_deg: float = 90.0
    straight_angle_deg: float = 180.0


@dataclass(frozen=True)
class ReportAllowables:
    """Workbook-labelled criteria; provenance is not stated in the workbook."""

    moonpool_minimum_bend_radius_m: float
    layspan_minimum_bend_radius_m: float
    moonpool_clearance_criterion_m: str
    tulip_contact_load_kn: float

    def summary_values(self) -> Tuple[Scalar, ...]:
        """Allowable row H:AA; blank direct references become numeric zero."""
        return (
            "/", "/", "/", "/", "/", "/",
            self.moonpool_minimum_bend_radius_m,
            self.layspan_minimum_bend_radius_m,
            self.moonpool_clearance_criterion_m,
            self.tulip_contact_load_kn, "/", "/",
        ) + (0.0,) * 8


@dataclass(frozen=True)
class DynamicsRow:
    """Raw inputs in m, s, degrees, m/s and kN; factor is dimensionless.

    The filename contains the Hs and Tp tokens used by the workbook; the raw
    numeric Hmax and WavePeriod columns are deliberately not substituted.
    Supply all values in workbook units; convert before constructing inputs.
    """

    case_filename: str
    vessel_heading_deg: float
    wave_direction_deg: float
    reference_current_speed_m_per_s: float
    current_factor_dimensionless: float
    reference_current_direction_deg: float
    upper_tension_max_kn: float
    upper_tension_min_kn: float
    connection_tension_max_kn: float
    connection_tension_min_kn: float
    connection_declination_max_deg: float
    connection_declination_min_deg: float
    moonpool_minimum_bend_radius_m: float
    layspan_minimum_bend_radius_m: float
    moonpool_clearance_m: float
    contact_load_kn: float
    layspan_tension_max_kn: float
    layspan_tension_min_kn: float


@dataclass(frozen=True)
class ReportMetadata:
    """Caller-supplied title template and dimensionless report text.

    The template receives prefix, step and current_description fields. A None
    prefix omits the title. The sheet name supplies CELL(filename) context.
    """

    sheet_name: str
    current_description: str
    title_template: str
    title_prefix: Optional[str] = None


@dataclass(frozen=True)
class ReportRow:
    """Output units match DynamicsRow; wave_height_text_m stays text as in LEFT."""

    wave_period_s: int
    wave_direction_clockwise_from_north_deg: float
    wave_heading_relative_to_connection_deg: float
    wave_height_text_m: str
    surface_current_speed_m_per_s: float
    current_direction_clockwise_from_north_deg: float
    upper_tension_max_kn: float
    upper_tension_min_kn: float
    connection_tension_max_kn: float
    connection_tension_min_kn: float
    connection_angle_max_deg: float
    connection_angle_min_deg: float
    moonpool_minimum_bend_radius_m: float
    layspan_minimum_bend_radius_m: float
    moonpool_clearance_m: float
    contact_load_kn: float
    layspan_tension_max_kn: float
    layspan_tension_min_kn: float

    def response_values(self) -> Tuple[float, ...]:
        """The twelve response columns used in the report extrema."""
        return (
            self.upper_tension_max_kn, self.upper_tension_min_kn,
            self.connection_tension_max_kn, self.connection_tension_min_kn,
            self.connection_angle_max_deg, self.connection_angle_min_deg,
            self.moonpool_minimum_bend_radius_m, self.layspan_minimum_bend_radius_m,
            self.moonpool_clearance_m, self.contact_load_kn,
            self.layspan_tension_max_kn, self.layspan_tension_min_kn,
        )


@dataclass(frozen=True)
class BendingReport:
    """Reduced rows and summary columns H:AA in workbook units.

    The S8 label says kNm, but S is copied from raw minimum tension (kN).
    This discrepancy is preserved and documented rather than converted.
    """

    step_label: str
    title: Optional[str]
    rows: Tuple[ReportRow, ...]
    maxima: Tuple[float, ...]
    minima: Tuple[float, ...]
    allowables: Tuple[Scalar, ...]


def reduce_dynamics_row(
    raw: DynamicsRow, convention: DirectionConvention = DirectionConvention(),
) -> ReportRow:
    """Compute one repeated report row, without Excel or file access.

    Source: tests/modules/excel_utilities/excel_to_image.xlsx, all report
    sheets. No standard or clause is cited in the workbook. Filename parsing
    reproduces INT(LEFT(TEXTAFTER(...,"Tp"),4)) and LEFT(TEXTAFTER(...,"Hs"),4).
    Wave direction is not normalized; current adds one turn only when negative.
    """
    def token_after(delimiter: str) -> str:
        if delimiter not in raw.case_filename:
            raise ValueError(f"Missing filename token: {delimiter}")
        return raw.case_filename.split(delimiter, 1)[1][:FILENAME_VALUE_CHARACTERS]

    current_speed = raw.reference_current_speed_m_per_s * raw.current_factor_dimensionless
    current_direction = convention.north_offset_deg - raw.reference_current_direction_deg
    if current_speed > 0:
        if current_direction < 0:
            current_direction += convention.full_turn_deg
    else:
        current_direction = 0.0
    return ReportRow(
        math.floor(float(token_after("Tp"))),
        convention.full_turn_deg - raw.wave_direction_deg + convention.north_offset_deg,
        raw.wave_direction_deg - raw.vessel_heading_deg,
        token_after("Hs"), current_speed, current_direction,
        raw.upper_tension_max_kn, raw.upper_tension_min_kn,
        raw.connection_tension_max_kn, raw.connection_tension_min_kn,
        convention.straight_angle_deg - raw.connection_declination_min_deg,
        convention.straight_angle_deg - raw.connection_declination_max_deg,
        raw.moonpool_minimum_bend_radius_m, raw.layspan_minimum_bend_radius_m,
        raw.moonpool_clearance_m, raw.contact_load_kn,
        raw.layspan_tension_max_kn, raw.layspan_tension_min_kn,
    )


def calculate_bending_report(
    raw_rows: Tuple[DynamicsRow, ...], metadata: ReportMetadata,
    allowables: ReportAllowables,
    convention: DirectionConvention = DirectionConvention(),
) -> BendingReport:
    """Apply the one shared row calculation and reduce the response columns.

    Source: tests/modules/excel_utilities/excel_to_image.xlsx. All sixteen
    report sheets have identical normalized formulas. No standard or clause
    is cited in the workbook. Empty helper columns produce zero extrema.
    Sheet context is explicit rather than depending on Excel CELL(filename).
    """
    if "_" not in metadata.sheet_name:
        raise ValueError("Report sheet name needs an underscore for the step label")
    step = metadata.sheet_name.split("_", 1)[1][:REPORT_STEP_CHARACTERS]
    title = None if metadata.title_prefix is None else (
        metadata.title_template.format(
            prefix=metadata.title_prefix, step=step,
            current_description=metadata.current_description,
        )
    )
    rows = tuple(reduce_dynamics_row(raw, convention) for raw in raw_rows)
    columns = tuple(zip(*(row.response_values() for row in rows)))
    maxima = tuple(max(column) for column in columns) if rows else (0.0,) * 12
    minima = tuple(min(column) for column in columns) if rows else (0.0,) * 12
    return BendingReport(
        step, title, rows, maxima + (0.0,) * 8, minima + (0.0,) * 8,
        allowables.summary_values(),
    )
