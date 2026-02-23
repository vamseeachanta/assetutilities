# ABOUTME: Tests for LineageGraph unit-conversion lineage visualization.
# ABOUTME: Verifies graph construction from audit logs, node/edge extraction, and export.

import pytest

from assetutilities.units.quantity import TrackedQuantity
from assetutilities.units.traceability import CalculationAuditLog
from assetutilities.units.visualization import LineageGraph


@pytest.fixture
def simple_audit_log():
    """Audit log with 2 inputs, 1 step, 1 output."""
    log = CalculationAuditLog()
    log.add_input("pressure", TrackedQuantity(100.0, "Pa", source="gauge"))
    log.add_input("area", TrackedQuantity(2.0, "m**2", source="drawing"))
    log.add_step("force = pressure * area")
    log.add_output("force", TrackedQuantity(200.0, "N", source="calc"))
    return log


@pytest.fixture
def complex_audit_log():
    """Audit log with 3 inputs, 2 steps, 2 outputs."""
    log = CalculationAuditLog()
    log.add_input("pressure", TrackedQuantity(100.0, "Pa", source="gauge"))
    log.add_input("area", TrackedQuantity(2.0, "m**2", source="drawing"))
    log.add_input("density", TrackedQuantity(1025.0, "kg/m**3", source="spec"))
    log.add_step("force = pressure * area")
    log.add_step("stress = force / area")
    log.add_output("force", TrackedQuantity(200.0, "N", source="calc"))
    log.add_output("stress", TrackedQuantity(100.0, "Pa", source="calc"))
    return log


class TestLineageGraphCreation:
    def test_create_empty_graph(self):
        # Arrange & Act
        graph = LineageGraph()

        # Assert
        assert graph is not None
        assert graph.nodes == []
        assert graph.edges == []

    def test_from_audit_log(self, simple_audit_log):
        # Arrange — fixture provides the log

        # Act
        graph = LineageGraph.from_audit_log(simple_audit_log)

        # Assert
        node_names = [n["name"] for n in graph.nodes]
        assert "pressure" in node_names
        assert "area" in node_names
        assert "force" in node_names

    def test_empty_audit_log_produces_empty_graph(self):
        # Arrange
        log = CalculationAuditLog()

        # Act
        graph = LineageGraph.from_audit_log(log)

        # Assert
        assert graph.nodes == []
        assert graph.edges == []


class TestLineageGraphNodes:
    def test_nodes_property(self, simple_audit_log):
        # Arrange
        graph = LineageGraph.from_audit_log(simple_audit_log)

        # Act
        nodes = graph.nodes

        # Assert
        assert isinstance(nodes, list)
        for node in nodes:
            assert "name" in node
            assert "value" in node
            assert "unit" in node
            assert "role" in node
            assert node["role"] in ("input", "output")

    def test_nodes_have_correct_roles(self, simple_audit_log):
        # Arrange
        graph = LineageGraph.from_audit_log(simple_audit_log)

        # Act
        nodes_by_name = {n["name"]: n for n in graph.nodes}

        # Assert
        assert nodes_by_name["pressure"]["role"] == "input"
        assert nodes_by_name["area"]["role"] == "input"
        assert nodes_by_name["force"]["role"] == "output"

    def test_nodes_have_correct_values(self, simple_audit_log):
        # Arrange
        graph = LineageGraph.from_audit_log(simple_audit_log)

        # Act
        nodes_by_name = {n["name"]: n for n in graph.nodes}

        # Assert
        assert nodes_by_name["pressure"]["value"] == pytest.approx(100.0)
        assert nodes_by_name["area"]["value"] == pytest.approx(2.0)
        assert nodes_by_name["force"]["value"] == pytest.approx(200.0)


class TestLineageGraphEdges:
    def test_edges_property(self, simple_audit_log):
        # Arrange
        graph = LineageGraph.from_audit_log(simple_audit_log)

        # Act
        edges = graph.edges

        # Assert
        assert isinstance(edges, list)
        for edge in edges:
            assert "source" in edge
            assert "target" in edge
            assert "operation" in edge


class TestLineageGraphSerialization:
    def test_to_dict(self, simple_audit_log):
        # Arrange
        graph = LineageGraph.from_audit_log(simple_audit_log)

        # Act
        data = graph.to_dict()

        # Assert
        assert isinstance(data, dict)
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_to_dot(self, simple_audit_log):
        # Arrange
        graph = LineageGraph.from_audit_log(simple_audit_log)

        # Act
        dot_str = graph.to_dot()

        # Assert
        assert isinstance(dot_str, str)
        assert "digraph" in dot_str


class TestLineageGraphComplex:
    def test_from_audit_log_with_multiple_steps(self, complex_audit_log):
        # Arrange — fixture provides the log

        # Act
        graph = LineageGraph.from_audit_log(complex_audit_log)

        # Assert
        node_names = [n["name"] for n in graph.nodes]
        assert "pressure" in node_names
        assert "area" in node_names
        assert "density" in node_names
        assert "force" in node_names
        assert "stress" in node_names

        input_nodes = [n for n in graph.nodes if n["role"] == "input"]
        output_nodes = [n for n in graph.nodes if n["role"] == "output"]
        assert len(input_nodes) == 3
        assert len(output_nodes) == 2
