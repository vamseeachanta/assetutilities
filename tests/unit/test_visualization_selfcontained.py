"""Self-contained HTML and opt-in YAML provenance regressions.

Source: Plotly write_html API, include_plotlyjs parameter (accessed 2026-10-19):
https://plotly.com/python-api-reference/generated/plotly.io.write_html.html
True embeds the bundle; CDN mode needs network access. Tests inspect active
resource tags, since the bundled library itself contains unused CDN URL strings.
"""

from html import escape
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import pytest
import yaml

from assetutilities.common.validation import DataValidator
from assetutilities.common.visualization.visualization_xy import VisualizationXY
from assetutilities.common.yml_utilities import WorkingWithYAML

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/workflows/yaml_to_plot"


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.external = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script" and attributes.get("src"):
            self.external.append(attributes["src"])
        if tag == "link" and attributes.get("href"):
            self.external.append(attributes["href"])


def assert_self_contained(text):
    parser = Resources()
    parser.feed(text)
    assert not parser.external
    assert "plotly.js v" in text
    assert "Plotly.newPlot" in text


def test_xy_writer_embeds_plotly(tmp_path):
    (tmp_path / "Plot").mkdir()
    cfg = {
        "settings": {"file_name": "guard", "plt_save_extensions": [".html"]},
        "Analysis": {"result_folder": str(tmp_path)},
    }
    VisualizationXY().save_xy_plot_and_close_plotly(go.Figure(), cfg)
    assert_self_contained((tmp_path / "Plot/guard.html").read_text())


def test_validation_writer_embeds_plotly(tmp_path):
    validator = DataValidator()
    result = validator.validate_dataframe(pd.DataFrame({"x": []}))
    path = tmp_path / "validation.html"
    validator.generate_interactive_report(result, path)
    assert_self_contained(path.read_text())


def test_source_and_standards_do_not_request_cdn():
    for path in (ROOT / "src/assetutilities").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert 'include_plotlyjs="cdn"' not in text, path
        assert "include_plotlyjs='cdn'" not in text, path
    assert (
        "include_plotlyjs='cdn'"
        not in (ROOT / "docs/HTML_REPORTING_STANDARDS.md").read_text()
    )


@pytest.fixture
def report(tmp_path):
    html = tmp_path / "plot.html"
    html.write_text("<html><body>plot</body></html>")
    cfg = {"Analysis": {"CustomInputFile": str(EXAMPLE / "input.yml")}}
    return cfg, html


def test_provenance_uses_original_yaml_and_escapes_echo(report, tmp_path):
    cfg, path = report
    original = (EXAMPLE / "input.yml").read_text()
    original += '\n# <script>alert("example")</script>\n'
    input_path = tmp_path / "input.yml"
    input_path.write_text(original)
    cfg["Analysis"]["CustomInputFile"] = str(input_path)
    # Extraction has overwritten the live key chains with the raw arrays.
    cfg["data"] = {"groups_key_chain": [{"x": [[0, 1, 2]], "y": [[1, 3, 5]]}]}
    WorkingWithYAML()._append_plot_provenance(cfg, path)
    html = path.read_text()
    assert "assetutilities" in html
    assert "Generated (UTC)" in html
    assert "linear_response.yml" in html
    assert escape(original) in html
    assert str(tmp_path) not in html
    assert "<script>" not in html
    assert html.index("<details>") < html.index("</body>")


@pytest.mark.parametrize("input_file", [None, "missing.yml"])
def test_provenance_without_readable_input_keeps_plot(report, input_file):
    cfg, path = report
    cfg["Analysis"]["CustomInputFile"] = input_file
    before = path.read_text()
    WorkingWithYAML()._append_plot_provenance(cfg, path)
    text = path.read_text()
    assert "plot" in text
    if input_file is None:
        assert "Provenance" in text
        assert "<pre>" not in text
    else:
        assert text == before


def test_provenance_with_invalid_yaml_keeps_plot(report, tmp_path):
    cfg, path = report
    source = tmp_path / "invalid.yml"
    source.write_text("data: [")
    cfg["Analysis"]["CustomInputFile"] = str(source)
    before = path.read_bytes()
    WorkingWithYAML()._append_plot_provenance(cfg, path)
    assert path.read_bytes() == before


def test_provenance_without_body_marker_or_html(report):
    cfg, path = report
    path.write_text("plot fragment")
    WorkingWithYAML()._append_plot_provenance(cfg, path)
    assert path.read_text().startswith("plot fragment<details>")
    WorkingWithYAML()._append_plot_provenance(cfg, path.with_suffix(".absent"))
    assert not path.with_suffix(".absent").exists()


def test_example_extracts_independently_calculated_coordinates():
    """Chosen inputs: slope 2, intercept 1, x = 0, 1, 2 (dimensionless).

    Hand calculation: y(0)=2*0+1=1; y(1)=2*1+1=3; y(2)=2*2+1=5.
    These are synthetic inputs, not material constants or acceptance limits.
    No calculation is performed by the plotting workflow: it preserves values.
    """
    cfg = yaml.safe_load((EXAMPLE / "input.yml").read_text())
    cfg["Analysis"] = {"analysis_root_folder": str(EXAMPLE)}
    result = WorkingWithYAML().get_plotting_data(cfg)
    assert result["data"]["groups"][0]["x"] == [[0, 1, 2]]
    assert result["data"]["groups"][0]["y"] == [[1, 3, 5]]


def test_example_engine_offline_with_provenance(tmp_path, monkeypatch):
    """Run the committed example from a scratch copy; capture plotted values.

    Expected coordinates follow the hand calculation in the extraction test.
    """
    import shutil
    import socket

    from assetutilities.engine import engine

    example = tmp_path / "example"
    shutil.copytree(EXAMPLE, example, ignore=shutil.ignore_patterns("results", "logs"))
    monkeypatch.chdir(tmp_path)

    def no_network(*args, **kwargs):
        raise AssertionError("The example must run offline")

    monkeypatch.setattr(socket, "create_connection", no_network)
    original = VisualizationXY.save_xy_plot_and_close_plotly
    coordinates = []

    def capture(self, fig, cfg):
        coordinates.extend((list(trace.x), list(trace.y)) for trace in fig.data)
        original(self, fig, cfg)

    monkeypatch.setattr(VisualizationXY, "save_xy_plot_and_close_plotly", capture)
    engine(str(example / "input.yml"))
    text = (example / "results/Plot/input.html").read_text()
    assert coordinates == [([0, 1, 2], [1, 3, 5])]
    assert_self_contained(text)
    assert "Provenance &amp; input echo" in text
    assert "groups_key_chain" in text
    assert "linear_response.yml" in text
    assert str(tmp_path) not in text
