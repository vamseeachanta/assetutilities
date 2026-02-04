# ABOUTME: Tests for offshore domain field mappings and unit systems.
# ABOUTME: Validates offshore-specific field names map to correct quantity types.

from assetutilities.units.domains.offshore import (
    OFFSHORE_FIELD_MAP,
    OFFSHORE_UNIT_SYSTEMS,
)
from assetutilities.units.input_parser import FIELD_QUANTITY_MAP


class TestOffshoreFieldMap:
    def test_inherits_base_field_map(self):
        for key, value in FIELD_QUANTITY_MAP.items():
            assert key in OFFSHORE_FIELD_MAP
            assert OFFSHORE_FIELD_MAP[key] == value

    def test_wall_thickness_is_length(self):
        assert OFFSHORE_FIELD_MAP["wall_thickness"] == "length"

    def test_plate_thickness_is_length(self):
        assert OFFSHORE_FIELD_MAP["plate_thickness"] == "length"

    def test_stiffener_height_is_length(self):
        assert OFFSHORE_FIELD_MAP["stiffener_height"] == "length"

    def test_buckling_stress_is_stress(self):
        assert OFFSHORE_FIELD_MAP["buckling_stress"] == "stress"

    def test_von_mises_stress_is_stress(self):
        assert OFFSHORE_FIELD_MAP["von_mises_stress"] == "stress"

    def test_hoop_stress_is_stress(self):
        assert OFFSHORE_FIELD_MAP["hoop_stress"] == "stress"

    def test_hydrostatic_pressure_is_pressure(self):
        assert OFFSHORE_FIELD_MAP["hydrostatic_pressure"] == "pressure"

    def test_internal_pressure_is_pressure(self):
        assert OFFSHORE_FIELD_MAP["internal_pressure"] == "pressure"

    def test_external_pressure_is_pressure(self):
        assert OFFSHORE_FIELD_MAP["external_pressure"] == "pressure"

    def test_buoyancy_force_is_force(self):
        assert OFFSHORE_FIELD_MAP["buoyancy_force"] == "force"

    def test_tension_is_force(self):
        assert OFFSHORE_FIELD_MAP["tension"] == "force"

    def test_compression_is_force(self):
        assert OFFSHORE_FIELD_MAP["compression"] == "force"


class TestOffshoreUnitSystems:
    def test_has_same_systems_as_base(self):
        from assetutilities.units.input_parser import UNIT_SYSTEMS

        assert set(OFFSHORE_UNIT_SYSTEMS.keys()) == set(UNIT_SYSTEMS.keys())

    def test_si_system_has_length(self):
        assert "length" in OFFSHORE_UNIT_SYSTEMS["SI"]
        assert OFFSHORE_UNIT_SYSTEMS["SI"]["length"] == "m"

    def test_inch_system_has_stress(self):
        assert "stress" in OFFSHORE_UNIT_SYSTEMS["inch"]
        assert OFFSHORE_UNIT_SYSTEMS["inch"]["stress"] == "psi"
