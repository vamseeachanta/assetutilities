"""Offline contracts for repository-local security hooks."""

import json
import re
from pathlib import Path

import yaml

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9/3.10: supplied by pytest.
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[2]


def hooks():
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
    return {hook["id"]: hook for repo in config["repos"] for hook in repo["hooks"]}


def test_scanner_loads_default_rules_and_anchored_paths():
    config = tomllib.loads((ROOT / ".gitleaks.toml").read_text())
    assert config["extend"]["useDefault"] is True
    for path in config.get("allowlist", {}).get("paths", []):
        assert path.startswith("^") and (path.endswith("$") or path.endswith("/"))
        re.compile(path)


def test_scanner_hook_uses_local_configuration():
    assert hooks()["gitleaks"]["args"] == ["--config", ".gitleaks.toml"]
    assert (ROOT / ".gitleaks.toml").is_file()


def test_hook_entries_and_arguments_stay_in_repository():
    for hook in hooks().values():
        values = [hook.get("entry", ""), *hook.get("args", [])]
        assert all(not str(value).startswith("../") for value in values)


def test_bandit_baseline_is_local_and_empty():
    args = hooks()["bandit-staged"]["args"]
    baseline = args[args.index("-b") + 1]
    path = ROOT / baseline
    assert path.resolve().is_relative_to(ROOT.resolve())
    assert json.loads(path.read_text()) == {"results": [], "metrics": {}}
