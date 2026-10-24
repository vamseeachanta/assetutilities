"""Contract examples for the portable, offline agent configuration consumer."""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

from assetutilities.agent_os.agent_config import (
    bundle_agents,
    load_agents,
    main,
    parse_agents,
    render_prompt,
)

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "docs/modules/ai/_agents"


def write_yaml(tmp_path, text):
    path = tmp_path / "agents.yaml"
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    return path


@pytest.fixture
def agents():
    return [
        {
            "name": "python_programmer",
            "role": ["clean code", "maintainable code"],
            "principles": ["Write a regression test"],
        }
    ]


@pytest.mark.parametrize(
    "path",
    [
        CATALOG / name
        for name in (
            "agent_decision_making.yaml",
            "agent_devops_engineer.yaml",
            "agent_python_programmer.yaml",
            "multi_agent.yaml",
        )
    ],
    ids=lambda p: p.name,
)
def test_shipped_catalogs(path):
    assert load_agents(path)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "hello",
        "agents: []",
        "agents: {}",
        "- missing: name",
        "- name: Bad-Name\n  role: test",
        "- name: a\n  role: ''",
        "- name: a\n  role: [test, 42]",
        "- name: a\n  role: test\n  principles: text",
        "- name: a\n  role: test\n- name: a\n  role: other",
        "agents: []\nagents: []",
        "- name: a\n  name: b\n  role: test",
        "!!python/object/apply:builtins.print ['must not execute']",
        "- name: a\n  role: test\n  date: 2025-01-01",
        "- name: a\n  role: test\n  value: .nan",
        "- name: a\n  role: test\n  extra: {1: value}",
        "- &a {name: a, role: test, recursive: *a}",
        "agents: [{name: a, role: test}]\nignored: true",
    ],
)
def test_invalid_catalog_rejected(text):
    with pytest.raises(ValueError):
        parse_agents(text)


@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"], ids=["high", "low"])
@pytest.mark.parametrize("location", ["value", "key"])
@pytest.mark.parametrize("syntax", ["json", "yaml"])
@pytest.mark.parametrize("from_file", [False, True], ids=["memory", "file"])
def test_catalog_rejects_surrogates(
    agents, tmp_path, surrogate, location, syntax, from_file
):
    agents[0]["metadata"] = {
        "nested": [{surrogate: "text"} if location == "key" else surrogate]
    }
    text = json.dumps(agents)
    if syntax == "yaml":
        text = "agents: " + text
    with pytest.raises(ValueError, match="UTF-8"):
        if from_file:
            load_agents(write_yaml(tmp_path, text))
        else:
            parse_agents(text)


@pytest.mark.parametrize("operation", ["bundle", "render"])
@pytest.mark.parametrize("field", ["role", "principles", "metadata"])
def test_direct_catalog_apis_reject_surrogates(agents, operation, field):
    agents[0][field] = {
        "role": "test\ud800",
        "principles": ["test\udfff"],
        "metadata": {"nested": [{"\ud800": "text"}]},
    }[field]
    with pytest.raises(ValueError, match="UTF-8"):
        if operation == "bundle":
            bundle_agents(agents)
        else:
            render_prompt(agents, "python_programmer", "Task", {})


@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"], ids=["high", "low"])
@pytest.mark.parametrize("location", ["template", "input_value", "input_key"])
def test_direct_prompt_rejects_surrogates(agents, surrogate, location):
    template, inputs = {
        "template": ("Task " + surrogate, {}),
        "input_value": ("Task $task", {"task": surrogate}),
        "input_key": ("Task $task", {surrogate: "text"}),
    }[location]
    with pytest.raises(ValueError, match="UTF-8"):
        render_prompt(agents, "python_programmer", template, inputs)


@pytest.mark.parametrize(
    "text",
    [
        r'[{"name":"a","role":"\ud83d\ude80","metadata":{"\ud83d\ude80":"text"}}]',
        'agents: [{name: a, role: "\\U0001F680", metadata: {"\\U0001F680": text}}]',
    ],
    ids=["json", "yaml"],
)
def test_supplementary_strings_and_keys_remain_portable(text):
    agents = parse_agents(text)
    assert agents == [
        {"name": "a", "role": "\U0001f680", "metadata": {"\U0001f680": "text"}}
    ]
    assert parse_agents(bundle_agents(agents)) == agents
    assert render_prompt(
        agents, "a", "Task $task \U0001f680", {"task": "\U0001f680"}
    ) == ("# a\n\nRole: \U0001f680\n\nTask \U0001f680 \U0001f680\n")


def test_render_exact_prompt(agents):
    """Manual substitution: $task -> repair parser, $evidence -> failing test.

    The list role joins with '; '; each principle receives a '- ' prefix.
    Escaped $$ is a literal dollar. Values are not recursively substituted.
    """
    result = render_prompt(
        agents,
        "python_programmer",
        "Task: $task\nEvidence: ${evidence}\n$$",
        {"task": "repair parser", "evidence": "failing test"},
    )
    assert result == (
        "# python_programmer\n\nRole: clean code; maintainable code\n\n"
        "Principles:\n- Write a regression test\n\n"
        "Task: repair parser\nEvidence: failing test\n$\n"
    )


@pytest.mark.parametrize(
    "template,inputs",
    [
        ("$task", {}),
        ("$task", {"task": "test", "unused": "value"}),
        ("$task", {"task": 42}),
        ("$task", {"task": " "}),
        ("${task.attribute}", {}),
        ("$", {}),
        ("", {}),
        ("$task", ["task"]),
        ("$task", {1: "value"}),
    ],
)
def test_invalid_prompt_rejected(agents, template, inputs):
    with pytest.raises(ValueError):
        render_prompt(agents, "python_programmer", template, inputs)


def test_unknown_agent(agents):
    with pytest.raises(ValueError, match="Unknown agent"):
        render_prompt(agents, "missing", "Task", {})


def test_values_are_literal(agents):
    assert render_prompt(
        agents, "python_programmer", "$task", {"task": "$other"}
    ).endswith("$other\n")


def test_portable_bundle_round_trip(agents):
    text = bundle_agents(agents)
    assert json.loads(text) == {"agents": agents}
    assert parse_agents(text) == agents
    assert bundle_agents(agents) == text


@pytest.mark.parametrize(
    "value", [1e-7, 1e20, "before\u0085after", "before\u2028after", "\U0001f680"]
)
@pytest.mark.parametrize("from_file", [False, True], ids=["memory", "file"])
def test_bundle_preserves_metadata(agents, tmp_path, value, from_file):
    agents[0]["metadata"] = {"nested": [value]}
    text = bundle_agents(agents)
    if from_file:
        path = tmp_path / "bundle.json"
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        imported = load_agents(path)
    else:
        imported = parse_agents(text)
    assert imported == agents
    assert type(imported[0]["metadata"]["nested"][0]) is type(value)
    assert bundle_agents(imported) == text


@pytest.mark.parametrize(
    "text",
    [
        '[{"name":"a","name":"b","role":"test"}]',
        '[{"name":"a","role":"test","metadata":{"x":1,"\\u0078":2}}]',
        '{"agents":[{"name":"a","role":"test"}],"agents":[]}',
        '[{"name":"a","role":"test","metadata":NaN}]',
        '[{"name":"a","role":"test","metadata":Infinity}]',
        '[{"name":"a","role":"test","metadata":-Infinity}]',
        '[{"name":"a","role":"test","metadata":1e999}]',
    ],
)
@pytest.mark.parametrize("from_file", [False, True], ids=["memory", "file"])
def test_invalid_json_catalog_rejected(tmp_path, text, from_file):
    with pytest.raises(ValueError):
        if from_file:
            load_agents(write_yaml(tmp_path, text))
        else:
            parse_agents(text)


@pytest.mark.parametrize("from_file", [False, True], ids=["memory", "file"])
def test_json_utf8_bom_preserves_metadata(agents, tmp_path, from_file):
    agents[0]["metadata"] = {"value": 1e-7, "text": "before\u0085after"}
    text = "\ufeff" + bundle_agents(agents)
    if from_file:
        imported = load_agents(write_yaml(tmp_path, text))
    else:
        imported = parse_agents(text)
    assert imported == agents


def test_portable_bundle_in_memory(agents):
    text = bundle_agents(agents)
    assert json.loads(text) == {"agents": agents}
    assert text == bundle_agents(agents)


def test_bundle_accepts_dict_subclasses(agents):
    class AgentMapping(dict):
        pass

    assert json.loads(bundle_agents([AgentMapping(agents[0])])) == {"agents": agents}


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        [None],
        [{"name": "a"}],
        [{"name": "a", "role": "", "value": float("nan")}],
        [{"name": "a", "role": "test", "value": {1: "a"}}],
    ],
)
def test_bundle_rejects_invalid_agents(data):
    with pytest.raises(ValueError):
        bundle_agents(data)


def test_cli_validate_and_bundle(capsys, caplog):
    source = str(CATALOG / "multi_agent.yaml")
    assert main(["validate", source]) == 0
    assert "python_programmer" in capsys.readouterr().out
    assert main(["bundle", source]) == 0
    assert json.loads(capsys.readouterr().out)["agents"] == load_agents(source)
    assert not caplog.records


@pytest.mark.parametrize(
    "value",
    ["caf\u00e9", "\u2192", "\U0001f680"],
    ids=["accent", "arrow", "supplementary"],
)
def test_cli_redirected_bundle_is_utf8(tmp_path, agents, value):
    agents[0]["metadata"] = {"text": value}
    source = write_yaml(tmp_path, json.dumps(agents, ensure_ascii=False))
    result = run_legacy_cli("bundle", source)
    assert result.returncode == 0
    assert result.stderr == b""
    assert b"\r" not in result.stdout
    assert json.loads(result.stdout.decode("utf-8")) == {"agents": agents}
    output = tmp_path / "bundle.json"
    output.write_bytes(result.stdout)
    assert load_agents(output) == agents
    validated = run_legacy_cli("validate", output)
    assert validated.returncode == 0
    assert validated.stdout == b"python_programmer\n"
    assert validated.stderr == b""


@pytest.mark.parametrize(
    "value",
    ["caf\u00e9", "\u2192", "\U0001f680"],
    ids=["accent", "arrow", "supplementary"],
)
def test_cli_redirected_prompt_is_utf8(tmp_path, value):
    request = write_yaml(
        tmp_path,
        json.dumps(
            {
                "agent": "python_programmer",
                "template": "Task: $task",
                "inputs": {"task": value},
            },
            ensure_ascii=False,
        ),
    )
    result = run_legacy_cli("render", CATALOG / "multi_agent.yaml", request)
    assert result.returncode == 0
    assert result.stderr == b""
    assert b"\r" not in result.stdout
    assert result.stdout.decode("utf-8") == (
        "# python_programmer\n\nRole: Writes code in Python\n\n"
        "Principles:\n- clean code\n- DRY\n- keep it simple stupid\n- etc.\n\n"
        f"Task: {value}\n"
    )


def run_legacy_cli(*args):
    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONPATH": str(ROOT / "src")}
    env.pop("PYTHONUTF8", None)
    return subprocess.run(
        [sys.executable, "-m", "assetutilities.agent_os.agent_config", *map(str, args)],
        capture_output=True,
        env=env,
        cwd=ROOT,
    )


@pytest.mark.parametrize("syntax", ["json", "yaml"])
@pytest.mark.parametrize("location", ["value", "key"])
@pytest.mark.parametrize("command", ["validate", "bundle", "render"])
def test_cli_rejects_catalog_surrogates(tmp_path, agents, syntax, location, command):
    agents[0]["metadata"] = {"\ud800": "text"} if location == "key" else "\ud800"
    text = json.dumps(agents)
    if syntax == "yaml":
        text = "agents: " + text
    source = write_yaml(tmp_path, text)
    args = [command, source]
    if command == "render":
        args.append(ROOT / "examples/agent_prompt.yaml")
    result = run_legacy_cli(*args)
    assert result.returncode == 1
    assert result.stdout == b""
    assert result.stderr.startswith(b"Invalid configuration:")
    assert b"UTF-8" in result.stderr
    assert b"Traceback" not in result.stderr


@pytest.mark.parametrize("syntax", ["json", "yaml"])
@pytest.mark.parametrize(
    "location", ["agent", "template", "input_value", "input_key", "request_key"]
)
def test_cli_rejects_request_surrogates(tmp_path, syntax, location):
    request = {
        "agent": "python_programmer",
        "template": "Task $task",
        "inputs": {"task": "text"},
    }
    if location in {"agent", "template"}:
        request[location] = "\udfff"
    elif location == "request_key":
        request["\udfff"] = "text"
    else:
        request["inputs"] = (
            {"\udfff": "text"} if location == "input_key" else {"task": "\udfff"}
        )
    text = json.dumps(request)
    if syntax == "yaml":
        text = "---\n" + text
    source = write_yaml(tmp_path, text)
    result = run_legacy_cli("render", CATALOG / "multi_agent.yaml", source)
    assert result.returncode == 1
    assert result.stdout == b""
    assert result.stderr.startswith(b"Invalid configuration:")
    assert b"UTF-8" in result.stderr
    assert b"Traceback" not in result.stderr


def test_cli_worked_example(capsys):
    assert (
        main(
            [
                "render",
                str(CATALOG / "multi_agent.yaml"),
                str(ROOT / "examples/agent_prompt.yaml"),
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == (
        "# python_programmer\n\nRole: Writes code in Python\n\n"
        "Principles:\n- clean code\n- DRY\n- keep it simple stupid\n- etc.\n\n"
        "Task: Reject an empty configuration.\n"
        "Evidence: An empty mapping currently reaches the parser.\n"
        "First write a failing regression test, then propose the smallest fix.\n"
    )


@pytest.mark.parametrize(
    "text",
    [
        "[]",
        "agent: python_programmer",
        "agent: missing\ntemplate: test\ninputs: {}",
        "agent: python_programmer\ntemplate: test\ninputs: {}\nignored: value",
    ],
)
def test_cli_bad_request(tmp_path, capsys, caplog, text):
    request = write_yaml(tmp_path, text)
    assert main(["render", str(CATALOG / "multi_agent.yaml"), str(request)]) == 1
    captured = capsys.readouterr()
    assert not captured.out
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.name == "assetutilities.agent_os.agent_config"
    assert record.levelno == logging.ERROR
    assert record.getMessage().startswith("Invalid configuration:")


def test_missing_source(tmp_path, capsys, caplog):
    assert main(["validate", str(tmp_path / "missing.yaml")]) == 1
    assert not capsys.readouterr().out
    assert caplog.record_tuples == [
        (
            "assetutilities.agent_os.agent_config",
            logging.ERROR,
            "Invalid configuration: cannot read input file",
        )
    ]


@pytest.mark.parametrize("command", ["validate", "bundle", "render", "request"])
def test_cli_missing_input_reports_stderr(tmp_path, command):
    missing = tmp_path / "missing.yaml"
    args = [command, missing]
    if command == "render":
        args.append(ROOT / "examples/agent_prompt.yaml")
    elif command == "request":
        args = ["render", CATALOG / "multi_agent.yaml", missing]
    result = run_legacy_cli(*args)
    assert result.returncode == 1
    assert result.stdout == b""
    assert result.stderr == b"Invalid configuration: cannot read input file\n"
