"""Read-only inspection, detached and unborn HEADs; no test creates commits."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from git import Repo

from assetutilities.modules.git_utilities.git_utilities import GitUtilities


def test_real_checkout_from_subdirectory(tmp_path):
    """The checkout's own HEAD is an independent read-only comparison oracle."""
    root = Path(__file__).resolve().parents[3]
    with Repo(root) as repository:
        before = repository.head.commit.hexsha
    cfg = {
        "Analysis": {
            "analysis_root_folder": str(root / "examples/workflows/gitpython"),
            "result_folder": str(tmp_path),
        },
        "repos": [{"io": "."}],
        "common_cfg": {"commit": True, "push": True, "clone": True},
    }
    GitUtilities().router(cfg)
    report = yaml.safe_load((tmp_path / "gitpython_report.yml").read_text())
    assert report["repositories"][0]["head"] == before
    assert report["write_operations"] == "skipped: write operations not supported"
    with Repo(root) as repository:
        assert repository.head.commit.hexsha == before


@pytest.mark.parametrize("state", ["attached", "detached", "unborn"])
def test_repository_states_and_no_writes(tmp_path, state):
    """A supplied mock commit has literal sha/subject, with no Git writes."""
    repository = MagicMock()
    repository.__enter__.return_value = repository
    repository.head.is_valid.return_value = state != "unborn"
    repository.head.is_detached = state == "detached"
    repository.active_branch.name = "synthetic"
    repository.head.commit.hexsha = (
        "a" * 40
    )  # Synthetic object identifier, not a digest oracle.
    commit = MagicMock(hexsha="a" * 40, summary="Synthetic change")
    repository.iter_commits.return_value = [commit]
    repository.is_dirty.return_value = False
    cfg = {
        "Analysis": {"result_folder": str(tmp_path)},
        "repos": [{"io": "."}],
        "common_cfg": {"commit": True, "push": True, "clone": True},
    }
    with patch(
        "assetutilities.modules.git_utilities.git_utilities.Repo",
        return_value=repository,
    ):
        GitUtilities().router(cfg)
    row = cfg["gitpython"]["repositories"][0]
    assert row["current_branch"] == ("DETACHED" if state == "detached" else "synthetic")
    assert row["head"] == (None if state == "unborn" else "a" * 40)
    assert row["recent_commits"] == (
        [] if state == "unborn" else [{"sha": "a" * 40, "subject": "Synthetic change"}]
    )
    if state == "unborn":
        repository.iter_commits.assert_not_called()
    else:
        repository.iter_commits.assert_called_once_with(max_count=5)
    repository.index.commit.assert_not_called()
    repository.git.assert_not_called()
    repository.remote.assert_not_called()
    repository.clone.assert_not_called()
