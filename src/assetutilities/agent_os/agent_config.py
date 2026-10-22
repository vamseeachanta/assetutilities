"""Validate legacy agent YAML, render prompts and emit portable bundles offline.

These functions consume data only: no tools, models, commands or URLs are run.
The catalog contract and worked example are in docs/modules/ai/agents-index.md.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from string import Template
from typing import Any

import yaml


class _UniqueLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently retaining the last value."""


def _mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise ValueError("YAML mapping keys must be unique strings")
        result[key] = loader.construct_object(value_node)
    return result


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _json_data(value: Any, ancestors: tuple = ()) -> None:
    """Reject YAML-only types and cycles before a portable JSON export."""
    if isinstance(value, (dict, list)):
        if id(value) in ancestors:
            raise ValueError("Recursive data is not supported")
        ancestors = (*ancestors, id(value))
        if isinstance(value, dict):
            if any(not isinstance(key, str) for key in value):
                raise ValueError("Mapping keys must be strings")
            value = value.values()
        for item in value:
            _json_data(item, ancestors)
    elif (
        value is None
        or isinstance(value, (str, bool, int))
        or isinstance(value, float)
        and math.isfinite(value)
    ):
        return
    else:
        raise ValueError("Only finite JSON-compatible data is supported")


def _json_mapping(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON mapping keys must be unique strings")
        result[key] = value
    return result


def _parse_yaml(text: str) -> Any:
    """Preserve JSON values; use the YAML resolver only for non-JSON syntax."""
    try:
        try:
            data = json.loads(
                text.removeprefix("\ufeff"), object_pairs_hook=_json_mapping
            )
        except json.JSONDecodeError:
            data = yaml.load(text, Loader=_UniqueLoader)
        _json_data(data)
        return data
    except (yaml.YAMLError, UnicodeError, RecursionError) as exc:
        raise ValueError("Invalid YAML document") from exc


def _load_yaml(path: str | Path) -> Any:
    try:
        return _parse_yaml(Path(path).read_text(encoding="utf-8"))
    except UnicodeError as exc:
        raise ValueError("Input must be UTF-8 text") from exc


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(map(_text, value))


def _validate_agents(agents: Any) -> list[dict[str, Any]]:
    _json_data(agents)
    if not isinstance(agents, list) or not agents:
        raise ValueError("A nonempty list of agents is required")
    names = set()
    for agent in agents:
        if type(agent) is not dict:
            raise ValueError("Each agent must be a mapping")
        name = agent.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise ValueError("Agent names must be lowercase snake_case identifiers")
        if name in names:
            raise ValueError("Agent names must be unique")
        names.add(name)
        role = agent.get("role")
        if not (_text(role) or _text_list(role)):
            raise ValueError("Each agent needs a role string or nonempty string list")
        if "principles" in agent and not _text_list(agent["principles"]):
            raise ValueError("Principles must be a nonempty string list")
    return agents


def load_agents(path: str | Path) -> list[dict[str, Any]]:
    """Read either a legacy list or an ``agents`` wrapper; preserve metadata.

    Roles and principles are validated for prompt use. Other fields are opaque,
    JSON-compatible metadata, not validated executable task specifications.
    """
    return _catalog(_load_yaml(path))


def parse_agents(text: str) -> list[dict[str, Any]]:
    """Consume an in-memory YAML catalog or portable JSON bundle."""
    if not isinstance(text, str):
        raise TypeError("Catalog text must be a string")
    return _catalog(_parse_yaml(text))


def _catalog(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        if set(data) != {"agents"}:
            raise ValueError("A catalog wrapper must contain only 'agents'")
        data = data["agents"]
    return _validate_agents(data)


def _substitute(template: str, inputs: dict[str, str]) -> str:
    if not _text(template) or not isinstance(inputs, dict):
        raise ValueError("A nonempty template and input mapping are required")
    if any(not _text(key) or not _text(value) for key, value in inputs.items()):
        raise ValueError("Input keys and values must be nonempty strings")
    required = set()
    for match in Template.pattern.finditer(template):
        if match.group("invalid") is not None:
            raise ValueError("Invalid template placeholder")
        name = match.group("named") or match.group("braced")
        if name:
            required.add(name)
    if set(inputs) != required:
        raise ValueError("Inputs must exactly match the template placeholders")
    return Template(template).substitute(inputs)


def render_prompt(
    agents: list[dict[str, Any]],
    agent_name: str,
    template: str,
    inputs: dict[str, str],
) -> str:
    """Render literal substitutions with role and principles, without execution."""
    agents = _validate_agents(agents)
    agent = next((item for item in agents if item["name"] == agent_name), None)
    if agent is None:
        raise ValueError("Unknown agent")
    body = _substitute(template, inputs)
    role = agent["role"]
    if isinstance(role, list):
        role = "; ".join(role)
    sections = [f"# {agent_name}", f"Role: {role}"]
    if "principles" in agent:
        sections.append(
            "Principles:\n" + "\n".join(f"- {p}" for p in agent["principles"])
        )
    sections.append(body.rstrip("\n"))
    return "\n\n".join(sections) + "\n"


def bundle_agents(agents: list[dict[str, Any]]) -> str:
    """Return deterministic JSON, also readable as YAML by ``load_agents``."""
    return (
        json.dumps(
            {"agents": _validate_agents(agents)},
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )


def main(argv: list[str] | None = None) -> int:
    """Print validation names, a rendered prompt, or a portable bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "bundle", "render"):
        command = commands.add_parser(name)
        command.add_argument("catalog")
        if name == "render":
            command.add_argument("request", help="YAML with agent, template and inputs")
    args = parser.parse_args(argv)
    try:
        agents = load_agents(args.catalog)
        if args.command == "render":
            request = _load_yaml(args.request)
            if not isinstance(request, dict) or set(request) != {
                "agent",
                "template",
                "inputs",
            }:
                raise ValueError(
                    "A request must contain exactly agent, template and inputs"
                )
            output = render_prompt(
                agents, request["agent"], request["template"], request["inputs"]
            )
        elif args.command == "bundle":
            output = bundle_agents(agents)
        else:
            output = "\n".join(agent["name"] for agent in agents) + "\n"
    except OSError:
        print("Invalid configuration: cannot read input file", file=sys.stderr)
        return 1
    except (ValueError, RecursionError) as exc:
        print(f"Invalid configuration: {exc}", file=sys.stderr)
        return 1
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
