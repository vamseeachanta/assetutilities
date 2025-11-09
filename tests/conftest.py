<<<<<<< HEAD
"""
Pytest configuration helpers for AssetUtilities.

This file normalizes import paths so tests can load modules that live under the
``src`` and ``src/modules`` trees, and skips Windows or OrcaFlex specific
scenarios when they are executed on incompatible platforms.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Iterable

import pytest


def _unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    ordered: list[Path] = []
    for path in paths:
        resolved = str(path.resolve())
        if resolved not in seen:
            seen.add(resolved)
            ordered.append(Path(resolved))
    return ordered


def _extend_sys_path() -> None:
    project_root = Path(__file__).resolve().parent.parent
    src_dir = project_root / "src"
    modules_dir = src_dir / "modules"

    candidate_paths: list[Path] = [project_root, src_dir]

    if modules_dir.exists():
        candidate_paths.append(modules_dir)
        # Add each leaf directory that contains Python files so bare imports
        # like ``import ai_persistence_system`` keep working.
        for path in modules_dir.rglob("*.py"):
            candidate_paths.append(path.parent)

    for path in reversed(_unique_paths(candidate_paths)):
        sys.path.insert(0, str(path))


_extend_sys_path()


WINDOWS_ONLY_SEGMENTS = {
    "excel_utilities",
    "word_utilities",
    "file_edit",
    "file_management",
    "visualization",
    "yaml_utlities",
    "zip_utilities",
}

ORCAFLEX_SENTINELS = ("orcaflex", "orca_flex", "orcawave")


def pytest_ignore_collect(path, config):  # type: ignore[override]
    path_obj = Path(str(path))
    parts = {part.lower() for part in path_obj.parts}
    path_lower = path_obj.as_posix().lower()

    if any(sentinel in path_lower for sentinel in ORCAFLEX_SENTINELS):
        return True

    if not platform.system().lower().startswith("win") and parts & WINDOWS_ONLY_SEGMENTS:
        return True

    return False


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:  # noqa: D401
    """Skip Windows-specific and OrcaFlex-dependent tests on incompatible hosts."""

    is_windows = platform.system().lower().startswith("win")

    for item in items:
        path = Path(item.fspath.strpath)
        parts = {part.lower() for part in path.parts}

        if not is_windows and parts & WINDOWS_ONLY_SEGMENTS:
            item.add_marker(
                pytest.mark.skip(reason="Test requires Windows-specific Excel/Word stack"),
            )
            continue

        path_lower = path.as_posix().lower()
        if any(sentinel in path_lower for sentinel in ORCAFLEX_SENTINELS):
            item.add_marker(
                pytest.mark.skip(reason="Test depends on OrcaFlex tooling not available in CI"),
            )
=======
# ABOUTME: Pytest configuration file that adds tests directory to Python path
# ABOUTME: This enables all test files to import test_utils module

import sys
import pytest
from pathlib import Path

# Add tests directory to Python path so test_utils can be imported from subdirectories
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))


@pytest.fixture
def config_file():
    """
    Fixture providing a test configuration file path.
    Returns the path to a test YAML configuration file.
    """
    # Return a generic test config file path that can be overridden by tests
    return str(tests_dir / "test_config.yml")
>>>>>>> 87c2d3d25a267ba3796cb25f3cf033364ff0a980
