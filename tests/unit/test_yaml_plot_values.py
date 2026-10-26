# ABOUTME: Value assertions for the YAML plotting adapter using synthetic data.
# ABOUTME: Covers key-chain extraction and payload forwarding without rendering.

from copy import deepcopy
from pathlib import Path

import pytest

from assetutilities.common.yml_utilities import WorkingWithYAML


# Independent synthetic source: every expected array below cites this layout.
YAML_FIXTURE = """\
measurements:
  series:
    - samples:
        positions: [0.0, 1.5, 4.0]
        responses: [3.0, -2.0, 8.5]
        reference: [1.0, 2.5, 6.0]
    - samples:
        positions: [2.0, 5.0, 9.0]
        responses: [-1.0, 7.5, 0.0]
"""

# Indices cite YAML_FIXTURE.measurements.series: first and second entries.
PRIMARY_SERIES = 0
SECONDARY_SERIES = 1

EXPECTED_GROUPS = [
    {
        "label": "Primary responses",
        # YAML_FIXTURE.measurements.series[0].samples.positions.
        "x": [[0.0, 1.5, 4.0]],
        # YAML_FIXTURE.measurements.series[0].samples.responses and .reference.
        "y": [[3.0, -2.0, 8.5], [1.0, 2.5, 6.0]],
    },
    {
        "label": "Secondary responses",
        # YAML_FIXTURE.measurements.series[1].samples.positions.
        "x": [[2.0, 5.0, 9.0]],
        # YAML_FIXTURE.measurements.series[1].samples.responses.
        "y": [[-1.0, 7.5, 0.0]],
    },
]


def _keychain(series_index, field):
    return {
        "file_name": "data/measurements.yml",
        "key_chain": ["measurements", "series", series_index, "samples", field],
    }


@pytest.fixture
def yaml_plot_cfg(tmp_path, monkeypatch):
    """Create fresh config and YAML files outside the caller's working directory."""
    analysis_root = tmp_path / "analysis"
    data_dir = analysis_root / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "measurements.yml").write_text(YAML_FIXTURE, encoding="utf-8")
    plot_dir = analysis_root / "plots"
    plot_dir.mkdir()
    caller_dir = tmp_path / "caller"
    caller_dir.mkdir()
    monkeypatch.chdir(caller_dir)
    return {
        "Analysis": {
            "analysis_root_folder": str(analysis_root),
            "result_plot_folder": str(plot_dir),
            "file_name": "responses",
        },
        "settings": {
            "title": "Synthetic responses",
            "xlabel": "Position",
            "ylabel": "Response",
            "plt_engine": "plotly",
            "plt_save_extensions": [".html"],
            "legend": {"flag": False},
        },
        "data": {
            "type": "input",
            "groups_key_chain": [
                {
                    "label": "Primary responses",
                    "x": [_keychain(PRIMARY_SERIES, "positions")],
                    "y": [
                        _keychain(PRIMARY_SERIES, "responses"),
                        _keychain(PRIMARY_SERIES, "reference"),
                    ],
                },
                {
                    "label": "Secondary responses",
                    "x": [_keychain(SECONDARY_SERIES, "positions")],
                    "y": [_keychain(SECONDARY_SERIES, "responses")],
                },
            ],
        },
    }


def test_plot_arrays_match_yaml_fixture(yaml_plot_cfg):
    result = WorkingWithYAML().get_plotting_data(yaml_plot_cfg)

    # Expected arrays cite the literal YAML_FIXTURE paths in EXPECTED_GROUPS.
    assert result["data"]["groups"] == EXPECTED_GROUPS


def test_keychain_relative_to_analysis_root(yaml_plot_cfg):
    assert Path.cwd() != Path(yaml_plot_cfg["Analysis"]["analysis_root_folder"])
    file_keychain = _keychain(str(SECONDARY_SERIES), "positions")
    assert not Path(file_keychain["file_name"]).exists()
    utility = WorkingWithYAML()

    positions = utility.get_data_from_file_keychain(yaml_plot_cfg, file_keychain)
    responses = utility.get_data_from_file_keychain(
        yaml_plot_cfg, _keychain(str(SECONDARY_SERIES), "responses")
    )

    # YAML_FIXTURE.measurements.series[1].samples.positions and .responses.
    assert positions == [2.0, 5.0, 9.0]
    assert responses == [-1.0, 7.5, 0.0]


def test_keychain_missing_file(yaml_plot_cfg):
    file_keychain = _keychain(PRIMARY_SERIES, "positions")
    file_keychain["file_name"] = "data/absent.yml"
    expected_path = (
        Path(yaml_plot_cfg["Analysis"]["analysis_root_folder"])
        / file_keychain["file_name"]
    )

    with pytest.raises(FileNotFoundError) as error:
        WorkingWithYAML().get_data_from_file_keychain(yaml_plot_cfg, file_keychain)

    assert str(expected_path) in str(error.value)


def test_plot_adapter_forwards_values(yaml_plot_cfg, monkeypatch):
    import assetutilities.engine as engine_module

    captured_calls = []

    def capture_engine(*, inputfile, cfg, config_flag):
        captured_calls.append((inputfile, deepcopy(cfg), config_flag))

    monkeypatch.setattr(engine_module, "engine", capture_engine)
    caller_settings = deepcopy(yaml_plot_cfg["settings"])
    caller_analysis = deepcopy(yaml_plot_cfg["Analysis"])
    utility = WorkingWithYAML()
    cfg = utility.get_plotting_data(yaml_plot_cfg)
    utility.plot_yml_data(cfg)

    # Unpacking requires exactly one downstream payload for this adapter call.
    ((inputfile, payload, config_flag),) = captured_calls
    assert inputfile is None
    assert config_flag is False
    # Expected arrays cite the literal YAML_FIXTURE paths in EXPECTED_GROUPS.
    assert payload["data"]["groups"] == EXPECTED_GROUPS
    assert payload["data"]["type"] == "input"
    assert payload["Analysis"] == caller_analysis
    assert {key: payload["settings"][key] for key in caller_settings} == caller_settings
    assert payload["settings"]["file_name"] == str(
        Path(caller_analysis["result_plot_folder"]) / caller_analysis["file_name"]
    )
