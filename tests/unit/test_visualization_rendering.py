# ABOUTME: Tests for LineageGraph HTML/SVG rendering methods.
# ABOUTME: Covers to_svg(), to_html(), and graphviz-unavailable fallback.

from unittest.mock import patch

import pytest

from assetutilities.units import CalculationAuditLog, TrackedQuantity
from assetutilities.units.visualization import LineageGraph


@pytest.fixture
def sample_graph():
    """Build a graph from a simple audit log."""
    audit = CalculationAuditLog()
    audit.add_input("force", TrackedQuantity(500.0, "kN", source="load"))
    audit.add_input("area", TrackedQuantity(2.0, "m**2", source="section"))
    audit.add_step("stress = force / area")
    stress = TrackedQuantity(250.0, "kPa", source="calc")
    audit.add_output("stress", stress)
    return LineageGraph.from_audit_log(audit)


@pytest.fixture
def empty_graph():
    """Empty graph with no nodes or edges."""
    return LineageGraph.from_audit_log(CalculationAuditLog())


class TestToHtml:
    """LineageGraph.to_html produces standalone viewable HTML."""

    def test_html_contains_doctype(self, sample_graph):
        html = sample_graph.to_html()
        assert "<!DOCTYPE html>" in html or "<html" in html

    def test_html_contains_node_names(self, sample_graph):
        html = sample_graph.to_html()
        assert "force" in html
        assert "area" in html
        assert "stress" in html

    def test_html_contains_units(self, sample_graph):
        html = sample_graph.to_html()
        assert "kilonewton" in html or "kN" in html
        assert "meter" in html or "m ** 2" in html or "m²" in html

    def test_html_contains_roles(self, sample_graph):
        html = sample_graph.to_html()
        assert "input" in html.lower() or "Input" in html
        assert "output" in html.lower() or "Output" in html

    def test_html_empty_graph(self, empty_graph):
        html = empty_graph.to_html()
        assert "<html" in html

    def test_html_contains_edges(self, sample_graph):
        html = sample_graph.to_html()
        assert "stress = force / area" in html


class TestToSvg:
    """LineageGraph.to_svg renders SVG when graphviz is available."""

    def test_svg_without_graphviz_raises(self, sample_graph):
        with patch.dict("sys.modules", {"graphviz": None}):
            with pytest.raises(ImportError, match="graphviz"):
                sample_graph.to_svg()

    def test_svg_returns_string(self, sample_graph):
        try:
            import graphviz  # noqa: F401
        except ImportError:
            pytest.skip("graphviz not installed")
        svg = sample_graph.to_svg()
        assert isinstance(svg, str)
        assert "<svg" in svg


class TestToHtmlFallback:
    """HTML rendering works without graphviz installed."""

    def test_html_works_without_graphviz(self, sample_graph):
        # to_html should never require graphviz — it has a table fallback
        with patch.dict("sys.modules", {"graphviz": None}):
            html = sample_graph.to_html()
            assert "<html" in html
            assert "force" in html
