"""Keep identifying todo tags out of tracked text and diagnostics."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TAG_PATTERN = re.compile(r"#[0-9]{1,3}_[a-z]+")
RULE_NAME = "numbered-personal-todo-tag"
CONSULTATION_PATTERN = re.compile(r"#[a-z]+_consultation\b")
# Store only the removed tag's digest so its identifying text stays absent.
CONSULTATION_TAG_DIGEST = (
    "4301f02a8598fc94f3068879be8a62f0d4c9ebc063d5c3c32ec375ae333edf8a"
)
CONSULTATION_RULE_NAME = "client-consultation-todo-tag"


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
        if "\0" in text:
            continue
        if TAG_PATTERN.search(text):
            violations.append(f"{relative_path}: {RULE_NAME}")
        if any(
            hashlib.sha256(match.group().encode()).hexdigest()
            == CONSULTATION_TAG_DIGEST
            for match in CONSULTATION_PATTERN.finditer(text)
        ):
            violations.append(f"{relative_path}: {CONSULTATION_RULE_NAME}")
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
    "prefix, suffix",
    [
        ("#todo ", ""),
        ("", ""),
        ("#todo\n", ""),
        ("\udc80", ""),
        ("\r\n", "\r\n"),
        ("(", "),"),
    ],
    ids=[
        "same-line",
        "standalone",
        "separate-line",
        "legacy-encoding",
        "crlf",
        "punctuation",
    ],
)
def test_detects_consultation_tags_without_exposing_their_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, suffix: str
) -> None:
    tag = "#" + "example" + "_consultation"
    monkeypatch.setitem(
        globals(), "CONSULTATION_TAG_DIGEST", hashlib.sha256(tag.encode()).hexdigest()
    )
    path = tmp_path / "notes.txt"
    with path.open(
        "w", encoding="utf-8", newline="\n", errors="surrogateescape"
    ) as handle:
        handle.write(prefix + tag + suffix)

    assert _violations(tmp_path, [path.name]) == [
        "notes.txt: client-consultation-todo-tag"
    ]


def test_reports_both_rules_once_per_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tag = "#" + "example" + "_consultation"
    monkeypatch.setitem(
        globals(), "CONSULTATION_TAG_DIGEST", hashlib.sha256(tag.encode()).hexdigest()
    )
    path = tmp_path / "notes.txt"
    path.write_text(("#" + "12_maintainer " + tag + "\n") * 2, encoding="utf-8")

    assert _violations(tmp_path, [path.name]) == [
        "notes.txt: client-consultation-todo-tag",
        "notes.txt: numbered-personal-todo-tag",
    ]


def test_consultation_rule_allows_other_tags_and_skips_binary_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tag = "#" + "example" + "_consultation"
    monkeypatch.setitem(
        globals(), "CONSULTATION_TAG_DIGEST", hashlib.sha256(tag.encode()).hexdigest()
    )
    path = tmp_path / "notes.txt"
    path.write_text("#todo arrange consultation #other_consultation", encoding="utf-8")
    assert _violations(tmp_path, [path.name]) == []

    path.write_text("binary\0" + tag, encoding="utf-8")
    assert _violations(tmp_path, [path.name]) == []


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
