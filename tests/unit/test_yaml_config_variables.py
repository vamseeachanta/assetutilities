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
    default.write_text(
        'label: original\noutput: "{{ label }}.csv"\n', encoding="utf-8", newline="\n"
    )
    update = tmp_path / "update.yml"
    update.write_text("label: revised\n", encoding="utf-8", newline="\n")
    assert ymlInput(str(default), str(update))["output"] == "revised.csv"


def test_resolution_after_stream_merge(tmp_path):
    """The second document supplies label; substitution gives sample.csv."""
    source = tmp_path / "stream.yml"
    source.write_text(
        'output: "{{ label }}.csv"\n---\nlabel: sample\n',
        encoding="utf-8",
        newline="\n",
    )
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
    custom.write_text(
        'label: custom\ncopy: "{{ output }}"\n', encoding="utf-8", newline="\n"
    )
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
    """YAML 1.2.2 sections 3.2.2.2 and 7.1 describe shared alias nodes."""
    source = tmp_path / "recursive.yml"
    source.write_text(
        "label: sample\nnode: &node\n  self: *node\n", encoding="utf-8", newline="\n"
    )
    result = ymlInput(str(source))
    assert result["node"]["self"] is result["node"]


def test_engine_loads_example_through_standard_cfg_path(tmp_path, monkeypatch):
    """By hand: engine must return placeholder and results/sample.csv unchanged."""
    from assetutilities.engine import engine

    source = tmp_path / "variables.yml"
    source.write_text(
        EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
    )
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


@pytest.mark.parametrize("from_file", [False, True])
@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ("{% raw %}{{ label }}{% endraw %}", "{{ label }}"),
        ("{{ indirect }}", "{{ label }}"),
    ],
)
def test_embedded_engine_renders_once(tmp_path, from_file, template, expected):
    """File and mapping inputs retain literal braces after a single pass."""
    import yaml

    from assetutilities.engine import engine

    cfg = {
        "basename": "yaml_utilities",
        "label": "sample",
        "indirect": "{{ label }}",
        "copy": template,
        "default": {"log_level": "INFO", "config": {"overwrite": {"output": True}}},
        "file_management": {"flag": False},
    }
    original = deepcopy(cfg)
    if from_file:
        source = tmp_path / "input.yml"
        source.write_text(yaml.safe_dump(cfg), encoding="utf-8", newline="\n")
        result = engine(inputfile=str(source), embed=True, root_folder=str(tmp_path))
    else:
        result = engine(cfg=cfg, embed=True, root_folder=str(tmp_path))
    assert result["copy"] == expected
    assert cfg == original


@pytest.mark.parametrize("explicit_context", [False, True])
@pytest.mark.parametrize(
    "template",
    [
        '{{ nested.labels.append("changed") }}',
        '{{ nested.update({"label": "changed"}) }}',
    ],
)
def test_rendering_preserves_nested_context(template, explicit_context):
    """Templates cannot mutate caller lists or mappings through public methods."""
    context = {"nested": {"labels": [], "label": "sample"}, "output": template}
    original = deepcopy(context)
    result = resolve_placeholders(context, context if explicit_context else None)
    assert context == original
    assert result["nested"] == original["nested"]
    assert result["output"] == template


def test_embedded_rendering_preserves_nested_caller_data(tmp_path):
    """The automatic embedded render cannot append to caller-owned lists."""
    cfg = {
        "nested": {"labels": []},
        "output": '{{ nested.labels.append("changed") }}',
        "default": {"log_level": "INFO", "config": {"overwrite": {"output": True}}},
    }
    original = deepcopy(cfg)
    result = ConfigureApplicationInputs().configure_embed(cfg, "probe", str(tmp_path))
    assert cfg == original
    assert result["nested"] == original["nested"]


@pytest.mark.parametrize("loader", [ymlInput, WorkingWithYAML().ymlInput])
@pytest.mark.parametrize(
    ("entry", "key", "expected"),
    [("2024: annual", 2024, "annual"), ("on: push", True, "push")],
)
def test_loader_renders_with_non_string_root_keys(
    tmp_path, loader, entry, key, expected
):
    """Non-string YAML keys survive; the string label still renders once."""
    source = tmp_path / "mixed.yml"
    source.write_text(
        entry + '\nlabel: sample\noutput: "{{ label }}"\n',
        encoding="utf-8",
        newline="\n",
    )
    result = loader(source.as_posix())
    assert result[key] == expected
    assert result["output"] == "sample"


def test_application_merge_renders_with_non_string_root_keys(tmp_path):
    """The application loader accepts the same mixed-key context as YAML input."""
    manager = ConfigureApplicationInputs()
    manager.ApplicationInputFile = (tmp_path / "packaged.yml").as_posix()
    manager.ApplicationInputFile_dict = {
        2024: "annual",
        "label": "sample",
        "copy": "{{ label }}",
    }
    manager.customYaml = None
    manager.CustomInputs = None
    result = manager.generateYMLInput({}, {})
    assert result[2024] == "annual"
    assert result["copy"] == "sample"


def test_type_error_in_template_retains_literal():
    """An incompatible operation is rejected without discarding the input text."""
    template = "{{ 1 + 'sample' }}"
    assert resolve_placeholders({"output": template})["output"] == template


@pytest.mark.parametrize("loader", [ymlInput, WorkingWithYAML().ymlInput])
def test_loader_opt_out_keeps_templates_after_all_merges(tmp_path, loader):
    """Opting out preserves expressions, escaped braces and Jinja comments."""
    source = tmp_path / "source.yml"
    source.write_text(
        'label: original\ncopy: "{{ label }}"\nmath: "$10^{{3}}$"\n'
        'comment: "before{# keep #}after"\n---\nextra: stream\n',
        encoding="utf-8",
        newline="\n",
    )
    update = tmp_path / "update.yml"
    update.write_text("label: revised\n", encoding="utf-8", newline="\n")
    result = loader(source.as_posix(), update.as_posix(), resolve_placeholders=False)
    assert result == {
        "label": "revised",
        "copy": "{{ label }}",
        "math": "$10^{{3}}$",
        "comment": "before{# keep #}after",
        "extra": "stream",
    }


@pytest.mark.parametrize("contents_only", [False, True])
def test_comparison_reports_template_and_literal_as_different(tmp_path, contents_only):
    """Comparisons record the original string, rather than its rendered value."""
    import yaml

    source = tmp_path / "source.yml"
    target = tmp_path / "target.yml"
    source.write_text(
        'label: sample\ncopy: "{{ label }}"\n', encoding="utf-8", newline="\n"
    )
    target.write_text("label: sample\ncopy: sample\n", encoding="utf-8", newline="\n")
    cfg = {"file_name1": source.as_posix(), "file_name2": target.as_posix()}
    helper = WorkingWithYAML()
    if contents_only:
        cfg["map_list"] = {"file_name1": ["copy"], "file_name2": ["copy"]}
        helper.compare_yaml_file_contents_deepdiff(cfg)
    else:
        helper.compare_yaml_files_deepdiff(cfg)
    outputs = list(tmp_path.glob("wwyaml_*_values_changed.yml"))
    assert len(outputs) == 1
    changes = yaml.safe_load(outputs[0].read_text(encoding="utf-8"))
    assert list(changes.values()) == [
        {"old_value": "{{ label }}", "new_value": "sample"}
    ]


@pytest.mark.parametrize("helper", ["analyze_yaml_keys", "compare_yaml_root_keys"])
def test_key_helpers_do_not_render_template_values(tmp_path, helper):
    """Key-only analysis must not evaluate expressions stored as template data."""
    source = tmp_path / "keys.yml"
    source.write_text('value: "{{ 1 / 0 }}"\n', encoding="utf-8", newline="\n")
    operation = getattr(WorkingWithYAML(), helper)
    operation(*([source.as_posix()] * (2 if helper == "compare_yaml_root_keys" else 1)))


@pytest.mark.parametrize(
    "template", ["{% raw %}{{ label }}{% endraw %}", "{{ indirect }}"]
)
def test_placeholder_diagnostic_reports_already_resolved_value(template, capsys):
    """A diagnostic reports the single-pass result without rendering it again."""
    cfg = resolve_placeholders(
        {
            "label": "sample",
            "indirect": "{{ label }}",
            "placeholder_tests": {"method": template},
        }
    )
    assert WorkingWithYAML().test_variable_placeholder(cfg) == (True, "{{ label }}")
    assert (
        capsys.readouterr().out.strip()
        == "yml key placeholder is reusable: {{ label }}"
    )


@pytest.mark.parametrize(
    "loader", [ymlInput, WorkingWithYAML().load_yml_with_utf_8_sig]
)
def test_utf8_readers_accept_bom_and_non_ascii_text(tmp_path, loader):
    """Explicit UTF-8 reads retain non-ASCII YAML values and accept an initial BOM."""
    source = tmp_path / "unicode.yml"
    source.write_text("\ufefflabel: café\n", encoding="utf-8", newline="\n")
    assert loader(source.as_posix()) == {"label": "café"}
