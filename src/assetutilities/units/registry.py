# ABOUTME: Singleton pint UnitRegistry with custom engineering unit definitions.
# ABOUTME: Provides energy (BOE, MCF, MMBTU, etc.) and offshore (ksi) units.

import threading

import pint

_registry: pint.UnitRegistry | None = None
_lock = threading.Lock()


def _define_custom_units(ureg: pint.UnitRegistry) -> None:
    """Register custom energy and offshore engineering units."""

    # Energy units based on BTU
    ureg.define("barrel_of_oil_equivalent = 5.8e6 * BTU = BOE")
    ureg.define("thousand_cubic_feet = 1.028e6 * BTU = MCF")
    ureg.define("MMCF = 1000 * MCF")
    ureg.define("BCF = 1e6 * MCF")
    ureg.define("TCF = 1e9 * MCF")
    ureg.define("standard_cubic_foot = 1028 * BTU = SCF")
    ureg.define("MMBTU = 1e6 * BTU")
    ureg.define("therm = 1e5 * BTU")
    ureg.define("tonne_of_oil_equivalent = 3.968e7 * BTU = TOE")

    # Offshore units - ksi is already in pint as kip_per_square_inch,
    # so we skip defining it here.


def get_registry() -> pint.UnitRegistry:
    """Return the singleton UnitRegistry with custom engineering units.

    Thread-safe. The registry is created once and reused for all subsequent
    calls.
    """
    global _registry
    if _registry is None:
        with _lock:
            if _registry is None:
                ureg = pint.UnitRegistry()
                _define_custom_units(ureg)
                _registry = ureg
    return _registry
