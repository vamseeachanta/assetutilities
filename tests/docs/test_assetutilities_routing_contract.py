from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "src" / "assetutilities"
OPERATOR_MAP = ROOT / "docs" / "maps" / "assetutilities-operator-map.md"
REGISTRY = ROOT / "docs" / "registry" / "module-routing.yaml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _routing_dirs_from_git_tree() -> list[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-d", "--name-only", "HEAD", "src/assetutilities/"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    dirs = []
    for line in result.stdout.splitlines():
        name = Path(line).name
        if name == "tests" or name.startswith("__"):
            continue
        dirs.append(name)
    return sorted(dirs)


def _operator_map_modules() -> set[str]:
    text = _read(OPERATOR_MAP)
    modules = set()
    for line in text.splitlines():
        if not line.startswith("| `"):
            continue
        match = re.match(r"\| `([^`]+)` \|", line)
        if match:
            modules.add(match.group(1))
    return modules


def test_docs_readme_exists_and_routes_common_issue_types() -> None:
    docs_readme = ROOT / "docs" / "README.md"
    assert docs_readme.exists()

    text = _read(docs_readme)
    for required in [
        "Issue type",
        "Source path",
        "Tests path",
        "Docs path",
        "calculations",
        "file and YAML utilities",
        "unit conversion",
        "CLI and agent commands",
    ]:
        assert required in text


def test_docs_readme_states_curated_vs_raw_boundary() -> None:
    text = _read(ROOT / "docs" / "README.md")

    curated_paths = [
        "docs/README.md",
        "docs/maps/assetutilities-operator-map.md",
        "docs/registry/module-routing.yaml",
        "MODULE_STRUCTURE.md",
    ]
    raw_paths = ["docs/ref/", "docs/sub_data/", "docs/sub_hardware/"]

    assert all(path in text for path in curated_paths)
    assert any(path in text for path in raw_paths)
    assert "raw inventory" in text.lower()


def test_operator_map_covers_all_top_level_routing_dirs() -> None:
    assert OPERATOR_MAP.exists()
    assert _operator_map_modules() == set(_routing_dirs_from_git_tree())


def test_registry_covers_all_top_level_routing_dirs() -> None:
    assert REGISTRY.exists()
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    module_names = {module["name"] for module in registry["modules"]}

    assert registry["repo"] == "assetutilities"
    assert module_names == set(_routing_dirs_from_git_tree())


def test_module_structure_matches_observed_tree() -> None:
    text = _read(ROOT / "MODULE_STRUCTURE.md")

    for forbidden in ["`core/`", "`utils/`", "core/", "utils/"]:
        assert forbidden not in text
    for name in _routing_dirs_from_git_tree():
        assert f"`{name}/`" in text


def test_readme_no_stale_directory_claims() -> None:
    text = _read(ROOT / "README.md")

    assert "core/" not in text
    assert "utils/" not in text
    assert "docs/README.md" in text
    assert "docs/maps/assetutilities-operator-map.md" in text
    assert "docs/registry/module-routing.yaml" in text


def test_agents_md_links_canonical_surfaces() -> None:
    text = _read(ROOT / "AGENTS.md")

    assert "docs/README.md" in text
    assert "docs/maps/assetutilities-operator-map.md" in text
    assert "docs/registry/module-routing.yaml" in text
