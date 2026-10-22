"""Contract examples for the portable, offline agent configuration consumer."""

import json
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
    "value", [1e-7, 1e20, "before\u0085after", "before\u2028after"]
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


def test_cli_validate_and_bundle(capsys):
    source = str(CATALOG / "multi_agent.yaml")
    assert main(["validate", source]) == 0
    assert "python_programmer" in capsys.readouterr().out
    assert main(["bundle", source]) == 0
    assert json.loads(capsys.readouterr().out)["agents"] == load_agents(source)


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
def test_cli_bad_request(tmp_path, capsys, text):
    request = write_yaml(tmp_path, text)
    assert main(["render", str(CATALOG / "multi_agent.yaml"), str(request)]) == 1
    captured = capsys.readouterr()
    assert not captured.out
    assert captured.err.startswith("Invalid configuration:")


def test_missing_source(tmp_path, capsys):
    assert main(["validate", str(tmp_path / "missing.yaml")]) == 1
    assert not capsys.readouterr().out
