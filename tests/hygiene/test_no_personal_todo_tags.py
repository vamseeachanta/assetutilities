"""Keep identifying numbered todo tags out of tracked text and diagnostics."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TAG_PATTERN = re.compile(r"#[0-9]{1,3}_[a-z]+")
RULE_NAME = "numbered-personal-todo-tag"


def _tracked_paths(root: Path) -> list[str]:
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
    )
    return [os.fsdecode(path) for path in result.stdout.split(b"\0") if path]


def _violations(root: Path, paths: list[str]) -> list[str]:
    violations = []
    for relative_path in paths:
        path = root / relative_path
        if path.is_symlink() or not path.is_file():
            continue
        with path.open(
            encoding="utf-8", newline="\n", errors="surrogateescape"
        ) as handle:
            text = handle.read()
        if "\0" not in text and TAG_PATTERN.search(text):
            violations.append(f"{relative_path}: {RULE_NAME}")
    return sorted(violations)


def test_no_personal_todo_tags_in_tracked_text() -> None:
    violations = _violations(ROOT, _tracked_paths(ROOT))
    if violations:
        pytest.fail("\n".join(violations), pytrace=False)


@pytest.mark.parametrize(
    "prefix",
    ["#todo ", "", "#todo\n", "\udc80", "\r\n"],
    ids=["same-line", "standalone", "separate-line", "legacy-encoding", "crlf"],
)
def test_detects_tags_without_exposing_their_text(tmp_path: Path, prefix: str) -> None:
    tag = "#" + "12" + "_" + "maintainer"
    path = tmp_path / "notes.txt"
    with path.open(
        "w", encoding="utf-8", newline="\n", errors="surrogateescape"
    ) as handle:
        handle.write(prefix + tag)

    assert _violations(tmp_path, [path.name]) == [f"notes.txt: {RULE_NAME}"]


@pytest.mark.parametrize(
    "text",
    ["#todo retain the action", "binary\0#" + "1_name"],
    ids=["generic-todo", "binary"],
)
def test_allows_generic_todos_and_skips_binary_files(tmp_path: Path, text: str) -> None:
    path = tmp_path / "notes.txt"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

    assert _violations(tmp_path, [path.name]) == []


def test_tracked_paths_use_nul_delimiters_and_clear_git_bindings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("GIT_DIR", "unrelated-metadata")
    monkeypatch.setenv("GIT_WORK_TREE", "unrelated-tree")
    monkeypatch.setenv("GIT_COMMON_DIR", "unrelated-common-metadata")

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        assert args == ["git", "ls-files", "-z"]
        assert kwargs["cwd"] == tmp_path
        assert not any(key.startswith("GIT_") for key in kwargs["env"])
        return subprocess.CompletedProcess(args, 0, b"space name.txt\0line\nname.txt\0")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert _tracked_paths(tmp_path) == ["space name.txt", "line\nname.txt"]
