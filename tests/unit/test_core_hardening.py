"""Core boundaries use synthetic inputs and independently specified answers.

No engineering constants or acceptance tolerances are introduced. YAML merge
answers follow the literal key assignments in each input. Log counts follow
the number of explicit emission calls, with exactly one output per call.
"""

import copy
import logging
from pathlib import Path

import pytest
import yaml

from assetutilities.common.logging_setup import logger, setup_logging
from assetutilities.common.set_logging import set_logging
from assetutilities.common.yml_utilities import (
    WorkingWithYAML,
    resolve_config_placeholders,
    resolve_placeholders,
)


def test_log_directory_creation_tolerates_a_concurrent_creator(tmp_path, monkeypatch):
    from assetutilities.common import ApplicationManager

    folder = tmp_path / "logs"
    folder.mkdir()
    exists = ApplicationManager.os.path.exists
    # Another worker has created the directory after this worker observed absence.
    monkeypatch.setattr(
        ApplicationManager.os.path,
        "exists",
        lambda path: False if Path(path) == folder else exists(path),
    )
    manager = ApplicationManager.ConfigureApplicationInputs()
    manager.customYaml = None
    manager.CustomInputs = None
    manager.ApplicationInputFile = "input.yml"
    cfg = manager.get_application_configuration_parameters(
        None, "yaml_utilities", {}, root_folder=str(tmp_path)
    )
    assert Path(cfg["Analysis"]["log_folder"]) == folder
    assert folder.is_dir()


def test_null_yaml_options_leave_config_unchanged():
    cfg = {"yaml_options": None, "label": "{{ name }}", "name": "value"}
    assert resolve_config_placeholders(cfg) is cfg
    assert cfg["label"] == "{{ name }}"


def test_stream_error_does_not_return_partial_config(tmp_path):
    path = tmp_path / "invalid.yml"
    path.write_text("valid: yes\n---\ninvalid: [\n", encoding="utf-8", newline="\n")
    with pytest.raises(yaml.YAMLError):
        WorkingWithYAML().yml_read_stream(str(path))


def test_stream_rejects_python_tags_after_valid_document(tmp_path):
    path = tmp_path / "unsafe.yml"
    path.write_text(
        "valid: yes\n---\nvalue: !!python/name:builtins.str\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(yaml.constructor.ConstructorError):
        WorkingWithYAML().ymlInput(str(path))


def test_stream_merges_mappings_and_skips_empty_documents(tmp_path):
    """Later b replaces earlier b; nested a remains from the first document."""
    path = tmp_path / "stream.yml"
    path.write_text(
        "nested: {a: first, b: old}\n---\n---\nnested: {b: new}\n",
        encoding="utf-8",
        newline="\n",
    )
    assert WorkingWithYAML().ymlInput(str(path)) == {
        "nested": {"a": "first", "b": "new"}
    }


def test_round_trip_loader_rejects_python_tags(tmp_path):
    from assetutilities.modules.yml_utilities.ruamel_yaml import RuamelYAML

    path = tmp_path / "unsafe.yml"
    path.write_text(
        "value: !!python/name:builtins.str\n", encoding="utf-8", newline="\n"
    )
    with pytest.raises(yaml.constructor.ConstructorError):
        RuamelYAML().load_clean_yaml_file(str(path))


@pytest.mark.parametrize(
    "key", ["../../escaped", "nested/section", "nested\\section", ".."]
)
def test_split_keys_cannot_escape_output_directory(tmp_path, key):
    from assetutilities.modules.yml_utilities.ruamel_yaml import (
        split_yaml_file_by_primary_key,
    )

    path = tmp_path / "input.yml"
    path.write_text(
        yaml.safe_dump({key: {"value": "unsafe"}}), encoding="utf-8", newline="\n"
    )
    with pytest.raises(ValueError, match="key"):
        split_yaml_file_by_primary_key(str(path), str(tmp_path / "output"))


@pytest.mark.parametrize("key", ["section one", "温度", 7, "section.one"])
def test_split_accepts_non_path_keys_and_preserves_utf8(tmp_path, key):
    from assetutilities.modules.yml_utilities.ruamel_yaml import (
        split_yaml_file_by_primary_key,
    )

    path = tmp_path / "input.yml"
    path.write_text(
        yaml.safe_dump({key: {"label": "温度"}}, allow_unicode=True),
        encoding="utf-8",
        newline="\n",
    )
    output = tmp_path / "output"
    rows = split_yaml_file_by_primary_key(path, output)
    expected = output / f"input_{key}.yml"
    assert rows == [{"data": expected.as_posix()}]
    raw = expected.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw
    assert yaml.safe_load(raw.decode("utf-8")) == {key: {"label": "温度"}}


def test_split_rejects_colliding_key_filenames_before_writing(tmp_path):
    from assetutilities.modules.yml_utilities.ruamel_yaml import (
        split_yaml_file_by_primary_key,
    )

    path = tmp_path / "input.yml"
    path.write_text(
        "7:\n  value: first\n'7':\n  value: second\n",
        encoding="utf-8",
        newline="\n",
    )
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="same filename"):
        split_yaml_file_by_primary_key(path, output)
    assert not list(output.glob("*.yml"))


def test_placeholder_resolution_is_opt_in_and_follows_updates(tmp_path):
    path = tmp_path / "config.yml"
    update = tmp_path / "update.yml"
    path.write_text(
        'name: old\nlabel: "prefix_{{ name }}"\n', encoding="utf-8", newline="\n"
    )
    update.write_text("name: new\n", encoding="utf-8", newline="\n")
    loader = WorkingWithYAML()
    assert loader.ymlInput(str(path))["label"] == "prefix_{{ name }}"
    assert loader.ymlInput(str(path), str(update), placeholders=True) == {
        "name": "new",
        "label": "prefix_new",
    }


def test_placeholder_lookup_uses_mapping_keys_before_attributes():
    assert (
        resolve_placeholders("{{ values.items }}", {"values": {"items": "ok"}}) == "ok"
    )


def test_cyclic_alias_is_rejected_without_recursing_forever():
    cfg = yaml.safe_load("cycle: &cycle [*cycle]\n")
    with pytest.raises(ValueError, match="Cyclic"):
        resolve_placeholders(cfg)


def test_engine_resolves_payload_placeholders_from_file(tmp_path, monkeypatch):
    from assetutilities.engine import engine
    from assetutilities.engine_registry import registry

    path = tmp_path / "input.yml"
    path.write_text(
        """basename: yaml_utilities
yaml_options: {resolve_placeholders: true}
name: resolved
label: "{{ name }}"
file_management: {flag: false}
""",
        encoding="utf-8",
        newline="\n",
    )
    received = []
    original = registry.resolve("yaml_utilities")

    def capture(cfg):
        received.append(cfg["label"])
        return original(cfg)

    monkeypatch.setitem(registry._handlers, "yaml_utilities", capture)
    result = engine(str(path), root_folder=str(tmp_path / "run"))
    assert received == ["resolved"]
    assert result["label"] == "resolved"
    assert (tmp_path / "run" / "results" / "input.yml").is_file()


def test_worked_yaml_plot_example(tmp_path):
    """Hand calculation: x*x is 0*0=0, 1*1=1, 2*2=4.

    The synthetic example supplies those coordinates as data. The engine must
    copy them unchanged into the plot, resolve its title and emit a PNG and cfg.
    """
    import shutil
    from pathlib import Path

    from assetutilities.engine import engine

    example = Path(__file__).resolve().parents[2] / "examples/workflows/core_hardening"
    inputs = tmp_path / "inputs"
    shutil.copytree(example, inputs)
    output = tmp_path / "output"
    # Input-relative sources remain next to the YAML; root_folder redirects
    # the engine's output and data roots, so copy the source into that root.
    output.mkdir()
    shutil.copy(inputs / "series.yml", output / "series.yml")
    cfg = engine(str(inputs / "input.yml"), root_folder=str(output))
    assert cfg["settings"]["title"] == "Synthetic square series"
    assert cfg["data"]["groups"] == [{"x": [[0, 1, 2]], "y": [[0, 1, 4]]}]
    assert (output / "results" / "Plot" / "input.png").is_file()
    assert (output / "results" / "input.yml").is_file()
    assert "application ... END" in (output / "logs" / "input.log").read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize(
    "text",
    [
        "{{ value.__class__ }}",
        "{{ helper() }}",
        "{{ cycler.__init__.__globals__ }}",
        "{% for item in values %}{{ item }}{% endfor %}",
    ],
)
def test_placeholders_do_not_evaluate_code_or_attributes(text):
    def helper():
        pytest.fail("Placeholder resolution called a function")

    context = {"helper": helper, "value": "text", "values": ["x"]}
    assert resolve_placeholders(text, context) == text


def test_plotting_retains_file_keychains_for_repeated_runs(tmp_path):
    """Literal x/y sequences are copied; extracting twice gives the same data."""
    (tmp_path / "series.yml").write_text(
        "x: [0, 1]\ny: [0, 2]\n", encoding="utf-8", newline="\n"
    )
    cfg = {
        "Analysis": {"analysis_root_folder": str(tmp_path)},
        "data": {
            "groups_key_chain": [
                {
                    "x": [{"file_name": "series.yml", "key_chain": ["x"]}],
                    "y": [{"file_name": "series.yml", "key_chain": ["y"]}],
                }
            ]
        },
    }
    original = copy.deepcopy(cfg["data"]["groups_key_chain"])
    loader = WorkingWithYAML()
    loader.get_plotting_data(cfg)
    loader.get_plotting_data(cfg)
    assert cfg["data"]["groups_key_chain"] == original
    assert cfg["data"]["groups"] == [{"x": [[0, 1]], "y": [[0, 2]]}]


@pytest.fixture
def isolated_logging():
    handlers = logging.root.handlers[:]
    level = logging.root.level
    yield
    logger.remove()
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        handler.close()
    logging.root.handlers[:] = handlers
    logging.root.setLevel(level)


@pytest.mark.parametrize("configure", [setup_logging, set_logging])
def test_both_logging_apis_write_each_message_once(
    tmp_path, isolated_logging, configure
):
    cfg = {
        "default": {"log_level": "INFO"},
        "Analysis": {"log_folder": str(tmp_path), "file_name": "run"},
    }
    assert configure(cfg) is cfg
    logger.info("native marker")
    logging.getLogger("consumer").warning("stdlib marker")
    logger.remove()
    text = (tmp_path / "run.log").read_text(encoding="utf-8")
    assert text.count("native marker") == 1
    assert text.count("stdlib marker") == 1
    assert " - INFO - native marker" in text


def test_logging_reconfiguration_closes_previous_run(tmp_path, isolated_logging):
    cfg = {
        "default": {"log_level": "WARNING"},
        "Analysis": {"log_folder": str(tmp_path), "file_name": "first"},
    }
    setup_logging(cfg)
    logger.warning("first marker")
    cfg["Analysis"]["file_name"] = "second"
    setup_logging(cfg)
    logging.getLogger("consumer").warning("second marker")
    logging.getLogger("consumer").info("filtered marker")
    logger.remove()
    assert "second marker" not in (tmp_path / "first.log").read_text(encoding="utf-8")
    text = (tmp_path / "second.log").read_text(encoding="utf-8")
    assert text.count("second marker") == 1
    assert "filtered marker" not in text


def test_setup_logging_honors_no_file_mode(tmp_path, isolated_logging):
    folder = tmp_path / "absent"
    cfg = {
        "Analysis": {
            "log_folder": str(folder),
            "file_name": "run",
            "log_to_file": False,
        }
    }
    setup_logging(cfg)
    logging.getLogger("consumer").warning("console marker")
    assert not folder.exists()
