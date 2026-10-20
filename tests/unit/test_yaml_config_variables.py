"""Config integration for #59; expected values use direct text substitution.

Syntax sources: YAML 1.2.2 (2021), sections 3.2.2.2 and 7.1;
Jinja 3.1 template documentation, Variables and Escaping. Fixture numbers
are arbitrary input data, not engineering constants or acceptance limits.
"""

from copy import deepcopy
from pathlib import Path

import pytest

from assetutilities.common.ApplicationManager import ConfigureApplicationInputs
from assetutilities.common.yml_utilities import (
    WorkingWithYAML,
    resolve_placeholders,
    ymlInput,
)

EXAMPLE = (
    Path(__file__).resolve().parents[2]
    / "docs/modules/yml_utilities/examples/variables.yml"
)


@pytest.mark.parametrize("loader", [ymlInput, WorkingWithYAML().ymlInput])
def test_loader_resolves_example(loader):
    """By hand: label=sample; output='results/' + 'sample' + '.csv'."""
    cfg = loader(str(EXAMPLE))
    assert cfg["data"]["groups"] == [
        {"label": "sample", "target": {"folder": "results"}}
    ]
    assert cfg["output"] == "results/sample.csv"
    assert cfg["placeholder_tests"]["method"] == "placeholder"
    assert cfg["placeholder_tests"]["library"] == "assetutilities"


def test_resolution_after_update_merge(tmp_path):
    """By hand: update changes label to revised, so output=revised.csv."""
    default = tmp_path / "default.yml"
    default.write_text('label: original\noutput: "{{ label }}.csv"\n')
    update = tmp_path / "update.yml"
    update.write_text("label: revised\n")
    assert ymlInput(str(default), str(update))["output"] == "revised.csv"


def test_resolution_after_stream_merge(tmp_path):
    """The second document supplies label; substitution gives sample.csv."""
    source = tmp_path / "stream.yml"
    source.write_text('output: "{{ label }}.csv"\n---\nlabel: sample\n')
    assert ymlInput(str(source))["output"] == "sample.csv"


def test_application_merge_uses_final_context(tmp_path):
    """By hand: argument label wins; base/{{ label }} becomes base/final."""
    manager = ConfigureApplicationInputs()
    manager.ApplicationInputFile = str(tmp_path / "packaged.yml")
    manager.ApplicationInputFile_dict = {
        "folder": "base",
        "output": "{{ folder }}/{{ label }}",
    }
    custom = tmp_path / "custom.yml"
    custom.write_text('label: custom\ncopy: "{{ output }}"\n')
    manager.customYaml = str(custom)
    manager.CustomInputs = None
    original = deepcopy(manager.ApplicationInputFile_dict)
    cfg = manager.generateYMLInput({}, {"label": "final"})
    assert cfg["output"] == "base/final"
    # One pass renders the original output value, without expanding it again.
    assert cfg["copy"] == "{{ folder }}/{{ label }}"
    assert manager.ApplicationInputFile_dict == original


def test_application_defaults_without_custom_file(tmp_path):
    """By hand: the packaged label is substituted even without custom input."""
    manager = ConfigureApplicationInputs()
    manager.ApplicationInputFile = str(tmp_path / "packaged.yml")
    manager.ApplicationInputFile_dict = {"label": "base", "copy": "{{ label }}"}
    manager.customYaml = None
    manager.CustomInputs = None
    assert manager.generateYMLInput({}, {})["copy"] == "base"


def test_embedded_configuration_resolves_before_filename(tmp_path):
    """By hand: meta.label becomes sample, so overwrite name is probe_sample."""
    cfg = {
        "label": "sample",
        "meta": {"label": "{{ label }}"},
        "default": {"log_level": "INFO", "config": {"overwrite": {"output": True}}},
    }
    original = deepcopy(cfg)
    result = ConfigureApplicationInputs().configure_embed(
        cfg, "probe", str(tmp_path), log_to_file=False
    )
    assert result["Analysis"]["file_name_for_overwrite"] == "probe_sample"
    assert cfg == original


def test_plain_scalars_and_template_newlines_preserved():
    """No YAML reparse: number and flag retain types; substitutions are strings."""
    data = {
        "number": 7,
        "flag": False,
        "nothing": None,
        "text": "plain\n",
        "copy": "{{ number }}\n",
        "yaml_text": "{{ value }}",
        "value": "yes: [a, b] # text",
    }
    result = resolve_placeholders(data)
    assert result == {**data, "copy": "7\n", "yaml_text": "yes: [a, b] # text"}
    assert result is not data


@pytest.mark.parametrize("value", ["{{ missing }}", "{{ invalid", "{{ ''.__class__ }}"])
def test_unresolved_invalid_and_unsafe_templates_remain_literal(value):
    """Undefined, malformed and sandbox-blocked expressions retain their text."""
    assert resolve_placeholders({"value": value}) == {"value": value}


def test_escaped_template_is_rendered_only_once():
    """Jinja Escaping: raw block prints literal braces, not the referenced value."""
    data = {"label": "sample", "copy": "{% raw %}{{ label }}{% endraw %}"}
    assert resolve_placeholders(data)["copy"] == "{{ label }}"


def test_recursive_alias_preserves_graph(tmp_path):
    """YAML 1.2.2 section 3.2.1 permits a node to contain itself."""
    source = tmp_path / "recursive.yml"
    source.write_text("label: sample\nnode: &node\n  self: *node\n")
    result = ymlInput(str(source))
    assert result["node"]["self"] is result["node"]


def test_engine_loads_example_through_standard_cfg_path(tmp_path, monkeypatch):
    """By hand: engine must return placeholder and results/sample.csv unchanged."""
    from assetutilities.engine import engine

    source = tmp_path / "variables.yml"
    source.write_text(EXAMPLE.read_text())
    monkeypatch.chdir(tmp_path)
    cfg = engine(inputfile=str(source), root_folder=str(tmp_path))
    assert cfg["output"] == "results/sample.csv"
    assert cfg["placeholder_tests"]["method"] == "placeholder"
    assert cfg["placeholder_tests"]["library"] == "assetutilities"
    assert list((tmp_path / "results").glob("*.yml"))


@pytest.mark.parametrize(
    "filename", ["variable_example_1.yml", "variable_example_2.yml"]
)
def test_original_issue_examples_load(filename):
    """By hand: both examples reuse the scalar defined at the document root."""
    source = (
        Path(__file__).resolve().parents[1]
        / "modules/yml_utilities/yml/variables"
        / filename
    )
    cfg = ymlInput(str(source))
    assert cfg["data"]["groups"][0]["label"] == cfg["define"]
