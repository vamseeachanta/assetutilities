"""Keep private personal references out of tracked text and diagnostics.

The stored SHA-256 digests cover only a 4-character and a 6-character prefix.
Either prefix can be recovered by brute force, so the digests keep
the words out of plain-text search but do not make them confidential.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PRIVATE_NAME_DIGEST = "229198ac50189365a5dd6412995ab24b4126c777fd69673153f92a0b1ba46882"
PRIVATE_SURNAME_DIGEST = (
    "f520df8438a87c99ba3ea1738359a7118ac5687f8544234da1ad3eacf32463a1"
)
PRIVATE_NAME_DIGESTS = ((4, PRIVATE_NAME_DIGEST), (6, PRIVATE_SURNAME_DIGEST))
RULE = "private-person-name"


def _contains_name(
    data: bytes, digests: tuple[tuple[int, str], ...] = PRIVATE_NAME_DIGESTS
) -> bool:
    if b"\0" in data:
        return False
    text = data.decode("utf-8", errors="surrogateescape")
    return any(
        hashlib.sha256(word.casefold()[:length].encode("utf-8")).hexdigest() == digest
        for word in set(re.findall(r"[^\W_]+", text))
        for length, digest in digests
    )


def _private_name_files(
    root: Path, digests: tuple[tuple[int, str], ...] = PRIVATE_NAME_DIGESTS
) -> list[str]:
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
        if _contains_name(data, digests):
            matches.append(
                "/".join(
                    "[redacted]" if _contains_name(os.fsencode(part), digests) else part
                    for part in relative.split("/")
                )
            )
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
        (b"restricted_suffix", True),
        ("restricted\u00e9".encode(), True),
        (b"RESTRICTEDcompound", True),
        (b"13_RESTRICTED_tag", True),
        (b"restricted2", True),
        (b"suffix_restricted", True),
        (b"unrestricted", False),
        (b"restrict", False),
        (b"\xff restricted", True),
        (b"\0restricted", False),
    ],
)
def test_private_name_rule_matches_token_prefixes(data: bytes, expected: bool) -> None:
    digest = hashlib.sha256(b"restricted").hexdigest()
    assert _contains_name(data, ((10, digest),)) is expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"restricted", True),
        (b"sealed", True),
        (b"SEALEDsuffix", True),
        (b"13_sealed_tag", True),
        (b"unsealed", False),
        (b"seale", False),
    ],
)
def test_private_name_rule_checks_both_name_digests(
    data: bytes, expected: bool
) -> None:
    digests = (
        (10, hashlib.sha256(b"restricted").hexdigest()),
        (6, hashlib.sha256(b"sealed").hexdigest()),
    )
    assert _contains_name(data, digests) is expected


@pytest.mark.parametrize(
    ("parts", "expected"),
    [
        (("RESTRICTEDcompound", "miniconda3"), ["tracked.md"]),
        (("restricted2", "AppData", "Local", "anaconda3"), ["tracked.md"]),
        (("13_RESTRICTED_tag",), ["tracked.md"]),
        (("SEALED",), ["tracked.md"]),
        (("sealedsuffix",), ["tracked.md"]),
        (("13_SEALED_tag",), ["tracked.md"]),
        (("unrestricted", "unsealed"), []),
        (("restrict", "seale"), []),
    ],
)
def test_tracked_scanner_detects_compound_paths_and_tags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    parts: tuple[str, ...],
    expected: list[str],
) -> None:
    # A matching directory name must not contaminate the negative controls.
    tmp_path = tmp_path / "restricted"
    tmp_path.mkdir()
    # Build path-like content at runtime so no host directory is embedded here.
    (tmp_path / "tracked.md").write_text("/".join(parts), encoding="utf-8")
    (tmp_path / "untracked.md").write_text("restricted sealed", encoding="utf-8")

    def tracked_files(command: list[str], **kwargs: object):
        assert command == ["git", "ls-files", "-z"]
        assert kwargs["cwd"] == tmp_path
        return subprocess.CompletedProcess(command, 0, stdout=b"tracked.md\0")

    monkeypatch.setattr(subprocess, "run", tracked_files)
    digests = (
        (10, hashlib.sha256(b"restricted").hexdigest()),
        (6, hashlib.sha256(b"sealed").hexdigest()),
    )
    assert _private_name_files(tmp_path, digests) == expected


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
    assert _private_name_files(tmp_path, ((10, digest),)) == ["tracked.md"]
    assert all(os.environ[key] == "unrelated-checkout" for key in keys)


@pytest.mark.parametrize(
    ("relative", "redacted"),
    [
        ("docs/RESTRICTEDcompound/notes.md", "docs/[redacted]/notes.md"),
        ("docs/13_SEALED_tag.md", "docs/[redacted]"),
        ("restricted/SEALED.md", "[redacted]/[redacted]"),
        ("docs/safe_restricted.md", "docs/[redacted]"),
    ],
)
def test_failure_redacts_matching_components_and_keeps_ordinary_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
    redacted: str,
) -> None:
    ordinary = "docs/unrestricted_unsealed.md"
    for name in (relative, ordinary):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("restricted sealed", encoding="utf-8")

    def tracked_files(command: list[str], **kwargs: object):
        assert command == ["git", "ls-files", "-z"]
        assert kwargs["cwd"] == tmp_path
        data = os.fsencode(relative) + b"\0" + os.fsencode(ordinary) + b"\0"
        return subprocess.CompletedProcess(command, 0, stdout=data)

    monkeypatch.setattr(subprocess, "run", tracked_files)
    digests = (
        (10, hashlib.sha256(b"restricted").hexdigest()),
        (6, hashlib.sha256(b"sealed").hexdigest()),
    )
    matches = _private_name_files(tmp_path, digests)
    monkeypatch.setitem(globals(), "_private_name_files", lambda root: matches)
    with pytest.raises(pytest.fail.Exception) as failure:
        test_tracked_text_has_no_private_name()
    message = str(failure.value)
    assert message == f"{RULE}: " + ", ".join(sorted((redacted, ordinary)))
    assert not _contains_name(message.encode(), digests)
