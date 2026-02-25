# ABOUTME: Life cycle costing calculations per BS15663 Part 2 (2001) and
# ABOUTME: marine transportation cost modelling per O&G Marine Transportations 0030-4.

from typing import Sequence


def net_present_value(costs: Sequence[float], discount_rate: float) -> float:
    """Return the Net Present Value of a cost stream.

    Each element of ``costs`` is the cost incurred at the start of that year,
    beginning at year 0 (i.e. the first element is undiscounted).

    NPV = sum(C_t / (1 + r)^t)  for t = 0, 1, ..., len(costs) - 1

    Args:
        costs: Sequence of costs by year (year-0 first).
        discount_rate: Annual discount rate as a decimal (e.g. 0.08 for 8%).

    Returns:
        Net present value of the cost stream.
    """
    r = discount_rate
    return sum(c / (1.0 + r) ** t for t, c in enumerate(costs))


def levelized_cost(
    costs: Sequence[float],
    outputs: Sequence[float],
    discount_rate: float,
) -> float:
    """Return the Levelized Cost of Energy / Output (LCOE).

    LCOE = sum(C_t / (1+r)^t) / sum(Q_t / (1+r)^t)

    Args:
        costs: Sequence of costs by year.
        outputs: Sequence of output quantities by year (same length as costs).
        discount_rate: Annual discount rate as a decimal.

    Returns:
        Levelized cost per unit of output.
    """
    r = discount_rate
    disc_costs = sum(c / (1.0 + r) ** t for t, c in enumerate(costs))
    disc_output = sum(q / (1.0 + r) ** t for t, q in enumerate(outputs))
    return disc_costs / disc_output


def annual_equivalent_cost(npv: float, discount_rate: float, life_years: int) -> float:
    """Return the Annual Equivalent Cost (AEC) also known as the Capital Recovery Factor.

    AEC = NPV * r / (1 - (1 + r)^(-n))

    Args:
        npv: Net present value of all life cycle costs.
        discount_rate: Annual discount rate as a decimal.
        life_years: Asset service life in whole years.

    Returns:
        Uniform annual cost equivalent to the given NPV over the asset life.
    """
    r = discount_rate
    n = life_years
    return npv * r / (1.0 - (1.0 + r) ** (-n))


def maintenance_cost_mtbf(
    cost_per_event: float,
    mtbf_years: float,
    years: float,
) -> float:
    """Return the expected total maintenance cost using MTBF-based modelling.

    expected_maintenance_cost = cost_per_event / MTBF * years

    Args:
        cost_per_event: Cost incurred each time a maintenance event occurs.
        mtbf_years: Mean time between failures in years.
        years: Period of interest in years.

    Returns:
        Expected total maintenance cost over the specified period.
    """
    return cost_per_event / mtbf_years * years


def marine_transport_cost(
    mobilization: float,
    transit_day_rate: float,
    transit_days: float,
    demobilization: float,
) -> float:
    """Return the total marine transportation cost.

    total = mobilization + transit_day_rate * transit_days + demobilization

    Args:
        mobilization: One-off mobilization cost.
        transit_day_rate: Day rate while vessel is in transit.
        transit_days: Number of transit days (use effective_transit_days if
            weather downtime must be accounted for).
        demobilization: One-off demobilization cost.

    Returns:
        Total marine transportation cost.
    """
    return mobilization + transit_day_rate * transit_days + demobilization


def effective_transit_days(nominal_days: float, downtime_fraction: float) -> float:
    """Return the weather-adjusted effective number of transit days.

    effective_transit_days = nominal_days / (1 - downtime_fraction)

    A downtime_fraction of 0.20 means 20 % of calendar time is lost to weather,
    so the vessel needs 25 % more calendar days to complete the transit.

    Args:
        nominal_days: Planned transit duration in days under ideal conditions.
        downtime_fraction: Fraction of time lost to weather (0 <= fraction < 1).

    Returns:
        Effective transit days after accounting for weather downtime.

    Raises:
        ValueError: If downtime_fraction is outside [0, 1).
    """
    if downtime_fraction < 0.0 or downtime_fraction >= 1.0:
        raise ValueError(
            f"downtime_fraction must be in [0, 1); got {downtime_fraction}"
        )
    return nominal_days / (1.0 - downtime_fraction)


def total_installed_cost(
    equipment: float,
    transport: float,
    installation: float,
    commissioning: float,
    contingency: float,
) -> float:
    """Return the Total Installed Cost (TIC) of an asset.

    TIC = equipment + transport + installation + commissioning + contingency

    Args:
        equipment: Procurement cost of the equipment.
        transport: Marine / land transportation cost to site.
        installation: Offshore / onsite installation cost.
        commissioning: Pre-operational testing and commissioning cost.
        contingency: Risk-based contingency allowance.

    Returns:
        Total installed cost.
    """
    return equipment + transport + installation + commissioning + contingency
