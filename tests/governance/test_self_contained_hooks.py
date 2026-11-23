"""Offline contracts for repository-local security hooks."""

import json
import re
import shlex
from pathlib import Path, PureWindowsPath

import pytest
import yaml

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9/3.10: supplied by pytest.
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[2]


def hooks():
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
    return {hook["id"]: hook for repo in config["repos"] for hook in repo["hooks"]}


def assert_scanner_allowlists(config):
    if isinstance(config, dict):
        for key, value in config.items():
            if key in {"allowlist", "allowlists"}:
                tables = value if isinstance(value, list) else [value]
                for table in tables:
                    assert (
                        table.get("regexes", []) == []
                    ), "regex allow-list is forbidden"
                    assert table.get("paths", []) == [], "path allow-list is forbidden"
            assert_scanner_allowlists(value)
    elif isinstance(config, list):
        for value in config:
            assert_scanner_allowlists(value)


def test_scanner_loads_default_rules_without_allowlists():
    config = tomllib.loads((ROOT / ".gitleaks.toml").read_text())
    assert config["extend"]["useDefault"] is True
    assert_scanner_allowlists(config)


@pytest.mark.parametrize(
    "configuration",
    [
        {"allowlist": {"regexes": ["blocked-pattern"]}},
        {"allowlists": [{"regexes": ["blocked-pattern"]}]},
        {"rules": [{"allowlist": {"regexes": ["blocked-pattern"]}}]},
        {"rules": [{"allowlists": [{"regexes": ["blocked-pattern"]}]}]},
    ],
    ids=["global", "global-tables", "rule", "rule-tables"],
)
def test_scanner_rejects_regex_allowlists(configuration):
    with pytest.raises(AssertionError, match="regex allow-list is forbidden"):
        assert_scanner_allowlists(configuration)


def test_scanner_hook_uses_local_configuration():
    assert hooks()["gitleaks"]["args"] == ["--config", ".gitleaks.toml"]
    assert (ROOT / ".gitleaks.toml").is_file()


def assert_hook_paths_in_repository(hook):
    values = [*shlex.split(hook.get("entry", "")), *hook.get("args", [])]
    for value in values:
        value = str(value)
        if value.startswith("-"):
            value = value.partition("=")[2]
        if not value or not any(char in value for char in "/\\."):
            continue
        path = Path(value.replace("\\", "/"))
        assert not path.is_absolute() and not PureWindowsPath(value).is_absolute()
        assert (ROOT / path).resolve().is_relative_to(ROOT.resolve())


def test_hook_entries_and_arguments_stay_in_repository():
    for hook in hooks().values():
        assert_hook_paths_in_repository(hook)


@pytest.mark.parametrize(
    "value", ["/outside/config.toml", "../outside.toml", "config/../../outside.toml"]
)
@pytest.mark.parametrize("field", ["entry", "args"])
def test_hook_rejects_paths_outside_repository(value, field):
    hook = {field: [value] if field == "args" else value}
    with pytest.raises(AssertionError):
        assert_hook_paths_in_repository(hook)


def test_hook_accepts_embedded_parent_step_inside_repository():
    assert_hook_paths_in_repository({"args": ["config/../.gitleaks.toml"]})


def test_ci_scanner_archive_has_literal_checksum():
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/source-hygiene.yml").read_text()
    )
    step = next(
        step
        for step in workflow["jobs"]["source-hygiene"]["steps"]
        if step.get("name") == "Scan pull request commits for secrets"
    )
    script = step["run"]
    assert re.search(r"expected_sha256=[0-9a-fA-F]{64}(?:\s|$)", script)
    assert "_checksums.txt" not in script
    assert "sha256sum --check --strict" in script
    assert script.index("sha256sum --check --strict") < script.index("tar -xzf")


def test_bandit_baseline_is_local_and_empty():
    args = hooks()["bandit-staged"]["args"]
    baseline = args[args.index("-b") + 1]
    path = ROOT / baseline
    assert path.resolve().is_relative_to(ROOT.resolve())
    assert json.loads(path.read_text()) == {"results": [], "metrics": {}}
