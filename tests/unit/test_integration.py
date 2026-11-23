# ABOUTME: Integration tests for the full unit tracking lifecycle.
# ABOUTME: Verifies round-trip: config → parse → compute → format → audit.

import json

import pytest

from assetutilities.units import (
    CalculationAuditLog,
    TrackedQuantity,
    UnitMismatchError,
    UnitSystemPolicy,
    unit_checked,
)
from assetutilities.units.input_parser import parse_config_section
from assetutilities.units.output_formatter import FormatTemplate, UnitFormatter
from assetutilities.units.visualization import LineageGraph


class TestConfigToComputeRoundTrip:
    """Full lifecycle: parse config → compute → verify units preserved."""

    def test_parse_compute_output(self):
        # Arrange — simulate a YAML config
        config = {
            "thickness": 25.0,
            "width": 200.0,
            "youngs_modulus": 210000.0,
        }

        # Act — parse with metric_engineering system
        parsed = parse_config_section(
            config, unit_system="metric_engineering", source="plate_spec.yml"
        )

        @unit_checked(thickness="mm", width="mm", youngs_modulus="MPa", _return="MPa")
        def calc_slenderness_ratio(thickness, width, youngs_modulus):
            return youngs_modulus * (thickness / width) ** 2

        result = calc_slenderness_ratio(
            parsed["thickness"], parsed["width"], parsed["youngs_modulus"]
        )

        # Assert — result should be TrackedQuantity with MPa units
        assert isinstance(result, TrackedQuantity)
        assert str(result.units) == "megapascal"
        assert result.magnitude == pytest.approx(
            210000.0 * (25.0 / 200.0) ** 2
        )
        # Provenance chain: created (parse) → converted (decorator) → created (return)
        assert len(result.provenance) >= 3

    def test_si_to_imperial_round_trip(self):
        # Arrange — start in SI
        depth_si = TrackedQuantity(100.0, "m", source="survey")

        # Act — convert to imperial and back
        depth_ft = depth_si.to("ft")
        depth_back = depth_ft.to("m")

        # Assert — magnitude preserved within floating point
        assert depth_back.magnitude == pytest.approx(100.0, rel=1e-10)
        # Provenance: created + converted(ft) + converted(m)
        assert len(depth_back.provenance) == 3

    def test_parse_then_policy_enforce(self):
        # Arrange — parse in imperial
        config = {"thickness": 1.0, "pressure": 14.7}
        parsed = parse_config_section(config, unit_system="inch", source="us_input")

        # Act — enforce SI policy
        policy = UnitSystemPolicy(system="SI", auto_convert=True)
        thickness_si = policy.enforce(parsed["thickness"], "length")
        pressure_si = policy.enforce(parsed["pressure"], "pressure")

        # Assert
        assert str(thickness_si.units) == "meter"
        assert thickness_si.magnitude == pytest.approx(0.0254)
        assert str(pressure_si.units) == "pascal"
        assert pressure_si.magnitude == pytest.approx(101352.932, rel=1e-3)


class TestAuditLogLifecycle:
    """Full audit: log inputs → compute → log outputs → export → verify."""

    def test_full_audit_cycle(self):
        # Arrange
        audit = CalculationAuditLog()
        force = TrackedQuantity(500.0, "kN", source="load_case_3")
        area = TrackedQuantity(2.0, "m**2", source="section_data")

        # Act — record, compute, record
        audit.add_input("force", force)
        audit.add_input("area", area)
        audit.add_step("stress = force / area")
        stress = force.to("N") / area  # 250000 N/m² = 250000 Pa
        audit.add_output("stress", stress)

        # Assert — JSON round-trip
        json_str = audit.to_json()
        data = json.loads(json_str)
        assert "force" in data["inputs"]
        assert "area" in data["inputs"]
        assert "stress" in data["outputs"]
        assert len(data["steps"]) == 1

        # Assert — CSV export
        csv = audit.to_csv()
        lines = csv.strip().split("\n")
        assert lines[0] == "role,name,magnitude,unit"
        assert len(lines) == 4  # header + 2 inputs + 1 output

        # Assert — summary
        summary = audit.summary()
        assert "force" in summary
        assert "stress" in summary

    def test_audit_filter_and_names(self):
        # Arrange
        audit = CalculationAuditLog()
        audit.add_input("depth", TrackedQuantity(100.0, "m", source="survey"))
        audit.add_input("temp", TrackedQuantity(15.0, "degC", source="sensor"))
        audit.add_input("pressure", TrackedQuantity(101.3, "kPa", source="baro"))
        audit.add_output("density", TrackedQuantity(1025.0, "kg/m**3", source="calc"))

        # Act & Assert — name properties
        assert audit.input_names == ["depth", "temp", "pressure"]
        assert audit.output_names == ["density"]

        # Act & Assert — filter by unit
        meter_inputs = audit.filter_inputs(unit="m")
        assert "depth" in meter_inputs
        assert len(meter_inputs) == 1


class TestVisualizationLifecycle:
    """Build a lineage graph from a real computation audit."""

    def test_graph_from_computation(self):
        # Arrange — simulate hydrostatic pressure calculation
        audit = CalculationAuditLog()
        rho = TrackedQuantity(1025.0, "kg/m**3", source="seawater_density")
        g = TrackedQuantity(9.81, "m/s**2", source="gravity_constant")
        d = TrackedQuantity(100.0, "m", source="bathymetry")
        audit.add_input("rho", rho)
        audit.add_input("g", g)
        audit.add_input("d", d)
        audit.add_step("P = rho * g * d")
        p = rho * g * d
        audit.add_output("P", p)

        # Act
        graph = LineageGraph.from_audit_log(audit)
        dot = graph.to_dot()
        data = graph.to_dict()

        # Assert — graph structure
        assert len(graph.nodes) == 4  # 3 inputs + 1 output
        assert len(graph.edges) >= 3  # each input connects to output via step

        input_names = {n["name"] for n in graph.nodes if n["role"] == "input"}
        assert input_names == {"rho", "g", "d"}

        output_names = {n["name"] for n in graph.nodes if n["role"] == "output"}
        assert output_names == {"P"}

        # Assert — DOT export
        assert "digraph" in dot
        assert "rho" in dot
        assert "P" in dot

        # Assert — dict export
        assert "nodes" in data
        assert "edges" in data


class TestFormatterLifecycle:
    """Format computed results with templates."""

    def test_format_with_registered_templates(self):
        # Arrange
        formatter = UnitFormatter()
        formatter.register_template(
            "pressure", FormatTemplate(precision=1, notation="fixed")
        )
        formatter.register_template(
            "length", FormatTemplate(precision=3, notation="fixed")
        )

        pressure = TrackedQuantity(101325.0, "Pa", source="calc")
        depth = TrackedQuantity(123.4567, "m", source="survey")

        # Act
        p_str = formatter.format_quantity(pressure)
        d_str = formatter.format_quantity(depth)

        # Assert — pressure uses precision=1
        assert "101325.0" in p_str
        # Assert — length uses precision=3
        assert "123.457" in d_str

    def test_format_provenance_chain(self):
        # Arrange — build a value with rich provenance
        v = TrackedQuantity(1000.0, "mm", source="drawing")
        v_m = v.to("m")
        v_doubled = v_m * 2.0

        formatter = UnitFormatter()

        # Act
        output = formatter.format_with_provenance(v_doubled)

        # Assert — provenance trail visible
        assert "created" in output
        assert "converted" in output
        assert "multiply" in output
        assert "drawing" in output


class TestMismatchDetection:
    """Engineering scenarios where unit mismatches should be caught."""

    def test_adding_pressure_to_force_fails(self):
        pressure = TrackedQuantity(100.0, "kPa", source="gauge")
        force = TrackedQuantity(50.0, "kN", source="load_cell")
        with pytest.raises(UnitMismatchError, match="add"):
            pressure + force

    def test_subtracting_length_from_mass_fails(self):
        length = TrackedQuantity(10.0, "m", source="tape")
        mass = TrackedQuantity(5.0, "kg", source="scale")
        with pytest.raises(UnitMismatchError, match="subtract"):
            length - mass

    def test_mixed_system_add_succeeds(self):
        # kPa and psi are both pressure — should auto-convert
        metric = TrackedQuantity(100.0, "kPa", source="metric_gauge")
        imperial = TrackedQuantity(14.696, "psi", source="us_gauge")
        result = metric + imperial
        assert result.magnitude == pytest.approx(
            100.0 + 14.696 * 6.89476, rel=1e-3
        )

    def test_policy_strict_catches_wrong_system(self):
        policy = UnitSystemPolicy(system="SI", strict=True, auto_convert=False)
        length_inch = TrackedQuantity(39.37, "inch", source="us_drawing")
        with pytest.raises(ValueError, match="expected.*m"):
            policy.enforce(length_inch, "length")
