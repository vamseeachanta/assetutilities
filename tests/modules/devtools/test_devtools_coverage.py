"""
Coverage tests for assetutilities.devtools — focusing on functions testable
without a real repo checkout. File-system-heavy CLI entry points are excluded.
"""
import pytest
from pathlib import Path

from assetutilities.devtools.modernize_deps import (
    DependencyModernizer,
    find_python_repositories,
)
from assetutilities.devtools.propagate_commands import find_repositories


# ---------------------------------------------------------------------------
# DependencyModernizer — unit-testable methods
# ---------------------------------------------------------------------------
class TestDependencyModernizer:
    def test_init_sets_repo_path(self, tmp_path):
        dm = DependencyModernizer(tmp_path, backup=False)
        assert dm.repo_path == tmp_path

    def test_find_requirements_files_happy_path(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("requests==2.28.0\n")
        (tmp_path / "requirements-dev.txt").write_text("pytest\n")
        dm = DependencyModernizer(tmp_path, backup=False)
        found = dm.find_requirements_files()
        names = [p.name for p in found]
        assert "requirements.txt" in names
        assert "requirements-dev.txt" in names

    def test_find_requirements_files_empty_dir_returns_empty(self, tmp_path):
        dm = DependencyModernizer(tmp_path, backup=False)
        assert dm.find_requirements_files() == []

    def test_create_backup_skipped_when_disabled(self, tmp_path):
        dm = DependencyModernizer(tmp_path, backup=False)
        dm.create_backup()
        assert dm.backup_dir is None

    def test_create_backup_creates_tempdir(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        dm = DependencyModernizer(tmp_path, backup=True)
        dm.create_backup()
        assert dm.backup_dir is not None
        assert dm.backup_dir.exists()


# ---------------------------------------------------------------------------
# find_python_repositories — scans for dirs containing pyproject.toml
# ---------------------------------------------------------------------------
class TestFindPythonRepositories:
    def test_finds_repo_with_pyproject(self, tmp_path):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / "pyproject.toml").write_text("[project]\nname='x'\n")
        found = find_python_repositories(tmp_path)
        assert repo in found

    def test_skips_dir_without_pyproject(self, tmp_path):
        other = tmp_path / "notrepo"
        other.mkdir()
        (other / "readme.txt").write_text("hello")
        found = find_python_repositories(tmp_path)
        assert other not in found

    def test_empty_base_returns_empty(self, tmp_path):
        assert find_python_repositories(tmp_path) == []


# ---------------------------------------------------------------------------
# propagate_commands.find_repositories — scans for git repos
# ---------------------------------------------------------------------------
class TestFindRepositories:
    def test_finds_git_repo(self, tmp_path):
        repo = tmp_path / "repo1"
        repo.mkdir()
        (repo / ".git").mkdir()
        found = find_repositories(tmp_path)
        assert repo in found

    def test_skips_non_git_dir_by_default(self, tmp_path):
        notgit = tmp_path / "notgit"
        notgit.mkdir()
        found = find_repositories(tmp_path)
        assert notgit not in found

    def test_include_non_git_flag(self, tmp_path):
        notgit = tmp_path / "notgit"
        notgit.mkdir()
        (notgit / "pyproject.toml").write_text("[project]\nname='x'\n")
        found = find_repositories(tmp_path, include_non_git=True)
        assert notgit in found
