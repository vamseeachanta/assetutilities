"""Guard YAML fixture comments against local export provenance.

Scope and expected outcomes follow issue #132 (2026): identifying export
comments are private metadata; relative fixture references remain valid.
Payload path sanitization is outside this header-only slice.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/modules/yml_utilities/yml/test_data"
# Issue #132: reject network, drive and profile paths in fixture comments.
# These are lexical path forms, with no engineering coefficients or limits.
PRIVATE_PATH = re.compile(
    r"\\\\[^\\\s]+\\|(?<![\w])[a-z]:[\\/]|(?<!:)//[^/\s]+/"
    r"|/(?:home|users)/[^/\s]+(?:/|$)",
    re.IGNORECASE,
)


def _private_comment_lines(text: str) -> list[int]:
    return [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if line.lstrip().startswith("#") and PRIVATE_PATH.search(line)
    ]


def _fixture_findings(root: Path) -> list[str]:
    fixtures = sorted(
        path for path in root.rglob("*") if path.suffix.lower() in {".yml", ".yaml"}
    )
    assert fixtures, "No YAML fixtures found for the privacy guard"
    return [
        f"{path.relative_to(root)}:{number}: private-comment-path"
        for path in fixtures
        for number in _private_comment_lines(path.read_text(encoding="utf-8-sig"))
    ]


def test_yaml_fixture_comments_have_no_private_paths():
    assert _fixture_findings(FIXTURES) == []


@pytest.mark.parametrize(
    "path",
    [
        "\\\\" + "network\\share\\fixture.yml",
        "//" + "network/share/fixture.yml",
        "Q:" + "\\folder\\fixture.yml",
        "Q:" + "/folder/fixture.yml",
        "C:" + "\\Users" + "\\example\\fixture.yml",
        "/" + "home" + "/example/fixture.yml",
        "/Users" + "/example/fixture.yml",
    ],
    ids=["unc", "network", "drive-backslash", "drive-slash", "profile", "unix", "mac"],
)
def test_private_path_comments_are_rejected(path):
    """Hand check: the path is on the second line; only that comment fails."""
    assert _private_comment_lines("---\n# File: " + path + "\nkey: value") == [2]


@pytest.mark.parametrize(
    "comment",
    [
        "# Export metadata omitted for fixture privacy.",
        "# File: fixtures/template.yml",
        "# Source: https://example.invalid/reference",
        "# Ratio: a/b",
    ],
)
def test_neutral_comments_are_allowed(comment):
    """Hand check: none of these comments contains a private path form."""
    assert _private_comment_lines(comment) == []


def test_scan_includes_nested_yaml_and_redacts_diagnostics(tmp_path):
    """Hand check: each synthetic file has one path comment on its second line."""
    nested = tmp_path / "nested"
    nested.mkdir()
    for name in ("sample.yml", "sample.yaml"):
        (nested / name).write_text(
            "\ufeff---\n# File: " + "Q:" + "/folder/fixture.yml\nkey: value\n",
            encoding="utf-8",
        )
    assert _fixture_findings(tmp_path) == [
        "nested/sample.yaml:2: private-comment-path",
        "nested/sample.yml:2: private-comment-path",
    ]


def test_missing_fixtures_fail_closed(tmp_path):
    with pytest.raises(AssertionError, match="No YAML fixtures found"):
        _fixture_findings(tmp_path)


EXPORT_FIXTURES = sorted(FIXTURES.glob("Template_*.yml")) + sorted(
    FIXTURES.glob("L0[12]*.yml")
)


def test_export_fixture_payloads_are_unchanged():
    """Compare non-comment bytes with independent repository baseline digests.

    Source: origin/main at 3626a05b71442557df44168bf2ac962dd88205c7.
    For each original fixture, git show supplies the bytes; remove only lines
    whose whitespace-stripped content starts with '#', then compute SHA-256.
    The expected tuple follows the sorted template glob, then the sibling glob.
    No YAML reader or implementation under test supplies these expected values.
    This preserves numeric data, placeholders, duplicate keys and line endings
    without importing a solver or interpreting vendor-specific YAML syntax.
    """
    expected = (
        "71a840a4bcb174fcc3856821894c1a5702aa54dbef7a5873488e03738653049d",
        "79e31bb80355e5b5a27a42bcd034c9f098852547c52fb3ecd84b59e911babf80",
        "3e90e5162fac41ac90bb86c51d13e5ee5c6afdce550ec1bdd1a825f6e415aadb",
        "2055cf658554d7ef88829797ae48c9c7adac63c28aa5467da8cf7b318a74f54d",
        "e06a92f6310045d722c2afd489eee040761c82965d7ef12a2f3fb20fc7d19aef",
        "2a3195d2dc75622e9528cf4bb3d01b9387f56d0833e8d6c296e02942904724e1",
    )
    actual = []
    for fixture in EXPORT_FIXTURES:
        raw = fixture.read_bytes()
        payload = b"".join(
            line
            for line in raw.splitlines(keepends=True)
            if not line.lstrip().startswith(b"#")
        )
        actual.append(hashlib.sha256(payload).hexdigest())
    assert tuple(actual) == expected


def test_export_identity_comments_are_omitted():
    """Issue #132: exported file, user and machine fields must be omitted."""
    for fixture in EXPORT_FIXTURES:
        text = fixture.read_text(encoding="utf-8-sig")
        assert not re.search(r"(?m)^# (?:File|User|Machine):", text), fixture.name
