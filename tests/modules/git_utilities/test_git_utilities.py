"""Read-only inspection, detached and unborn HEADs; no test creates commits."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from git import Repo

from assetutilities.modules.git_utilities.git_utilities import GitUtilities


def test_temporary_repository_preserves_index(tmp_path, monkeypatch):
    """Inspection must preserve staged bytes and suppress optional index writes."""
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.delenv(key, raising=False)
    root = tmp_path / "repository"
    original_is_dirty = Repo.is_dirty

    def inspect_without_optional_locks(repository, *args, **kwargs):
        assert repository.git.environment().get("GIT_OPTIONAL_LOCKS") == "0"
        return original_is_dirty(repository, *args, **kwargs)

    monkeypatch.setattr(Repo, "is_dirty", inspect_without_optional_locks)
    with Repo.init(root) as repository:
        with (root / "sample.txt").open("w", encoding="utf-8", newline="\n") as stream:
            stream.write("synthetic input\n")
        repository.index.add(["sample.txt"])
        index = Path(repository.git_dir) / "index"
        before = index.read_bytes()
    (root / "nested").mkdir()
    cfg = {
        "Analysis": {
            "analysis_root_folder": (root / "nested").as_posix(),
            "result_folder": (tmp_path / "out").as_posix(),
        },
        "repos": [{"io": "."}],
        "common_cfg": {"commit": True, "push": True, "clone": True},
    }
    GitUtilities().router(cfg)
    report = yaml.safe_load(
        (tmp_path / "out/gitpython_report.yml").read_text(encoding="utf-8")
    )
    assert report["repositories"][0]["head"] is None
    assert report["repositories"][0]["is_dirty"] is True
    assert report["write_operations"] == "skipped: write operations not supported"
    assert index.read_bytes() == before


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
