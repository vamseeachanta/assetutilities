"""Keep private personal references out of tracked text and diagnostics."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PRIVATE_NAME_DIGEST = "229198ac50189365a5dd6412995ab24b4126c777fd69673153f92a0b1ba46882"
RULE = "private-person-name"


def _contains_name(data: bytes, digest: str = PRIVATE_NAME_DIGEST) -> bool:
    if b"\0" in data:
        return False
    text = data.decode("utf-8", errors="surrogateescape")
    return any(
        hashlib.sha256(word.casefold().encode("utf-8")).hexdigest() == digest
        for word in set(re.findall(r"\w+", text))
    )


def _private_name_files(root: Path, digest: str = PRIVATE_NAME_DIGEST) -> list[str]:
    environment = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        environment.pop(key, None)
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        env=environment,
        check=True,
        capture_output=True,
    )
    matches = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = os.fsdecode(raw_path)
        path = root / relative
        if path.is_symlink():
            data = os.fsencode(os.readlink(path))
        elif path.is_file():
            data = path.read_bytes()
        else:
            continue
        if _contains_name(data, digest):
            matches.append(relative)
    return sorted(matches)


def test_tracked_text_has_no_private_name() -> None:
    matches = _private_name_files(ROOT)
    if matches:
        pytest.fail(f"{RULE}: " + ", ".join(matches), pytrace=False)


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"restricted", True),
        (b"RESTRICTED's note", True),
        (b"a/restricted/file", True),
        (b"prestricted", False),
        (b"restricted_suffix", False),
        ("restricted\u00e9".encode(), False),
        (b"\xff restricted", True),
        (b"\0restricted", False),
    ],
)
def test_private_name_rule_uses_whole_words(data: bytes, expected: bool) -> None:
    digest = hashlib.sha256(b"restricted").hexdigest()
    assert _contains_name(data, digest) is expected


def test_rule_needs_no_source_tag_and_ignores_inherited_git_bindings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "tracked.md").write_text("RESTRICTED", encoding="utf-8")
    (tmp_path / "untracked.md").write_text("restricted", encoding="utf-8")
    keys = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")
    for key in keys:
        monkeypatch.setenv(key, "unrelated-checkout")

    def tracked_files(command: list[str], **kwargs: object):
        assert command == ["git", "ls-files", "-z"]
        assert kwargs["cwd"] == tmp_path
        assert not any(key in kwargs["env"] for key in keys)
        return subprocess.CompletedProcess(command, 0, stdout=b"tracked.md\0")

    monkeypatch.setattr(subprocess, "run", tracked_files)
    digest = hashlib.sha256(b"restricted").hexdigest()
    assert _private_name_files(tmp_path, digest) == ["tracked.md"]
    assert all(os.environ[key] == "unrelated-checkout" for key in keys)
