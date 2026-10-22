"""Guard text fixture comments and payloads against identifying export metadata.

Issue #132: reject local paths and export identities, allowing relative fixture
references, URLs and ratios. Diagnostics contain only file, line and kind.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests"
EXPORT_ROOT = FIXTURES / "modules/yml_utilities/yml/test_data"
BACKSLASH = chr(92)
FIXTURE_SUFFIXES = {
    "",
    ".yml",
    ".yaml",
    ".json",
    ".csv",
    ".txt",
    ".xml",
    ".ini",
    ".cfg",
    ".toml",
    ".bat",
    ".dat",
    ".md",
    ".puml",
    ".deck",
}
# Lexical patterns contain no original identifying values.
PRIVATE_PATTERNS = (
    (
        "user-profile path",
        re.compile(
            r"/(?:home|users)/[^/\s]+(?:/|$)|[a-z]:[\\/]users[\\/][^\\/\s]+",
            re.I,
        ),
    ),
    (
        "network path",
        re.compile(
            r"\\\\[a-z0-9_.-]+\\|(?<![:/\w])//[a-z0-9_.-]+/",
            re.I,
        ),
    ),
    ("drive path", re.compile(r"(?<![\w])[a-z]:[\\/]", re.I)),
    (
        "machine name pattern",
        re.compile(
            r"\b(?:ws-[0-9a-f]{2}|(?:desktop|laptop)-[a-z0-9-]+)\b",
            re.I,
        ),
    ),
)
# SHA-256 of case-folded export identity tokens, without original names.
IDENTITY_HASHES = {
    "machine name pattern": frozenset(
        {
            "00e880d1a9f21c5d68e26d15a2287548ce4580e43e2b0ad088e8851c897f575f",
            "f46852cf6a989104870443a75acc3e70eb6191c7c4175c63f9cf066d31a3b824",
        }
    ),
    "user name pattern": frozenset(
        {
            "1eea75079965b82e89db3dd4f61ba5f5c3f38a014d83d15991a4734571c9947e",
            "e38f5e16adc86d1f9c50c751c34abce9ff0fe82e0619a75d4aa5394ebdcaaa89",
        }
    ),
}


def _private_lines(text: str) -> list[tuple[int, str]]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        kinds = {kind for kind, pattern in PRIVATE_PATTERNS if pattern.search(line)}
        tokens = re.findall(r"[a-z0-9_.-]+", line.casefold())
        digests = {
            hashlib.sha256(token.encode("utf-8")).hexdigest() for token in tokens
        }
        kinds.update(
            kind for kind, hashes in IDENTITY_HASHES.items() if hashes & digests
        )
        findings.extend((number, kind) for kind in sorted(kinds))
    return findings


def _is_link(path: Path) -> bool:
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def _fixture_findings(root: Path) -> list[str]:
    assert not _is_link(root), "Fixture root must not be a link"
    fixtures = []
    findings = []
    for directory, directories, names in os.walk(root, followlinks=False):
        parent = Path(directory)
        for name in sorted(directories):
            path = parent / name
            if _is_link(path):
                findings.append(
                    f"{path.relative_to(root).as_posix()}:0: linked directory"
                )
                directories.remove(name)
        for name in sorted(names):
            path = parent / name
            if path.suffix.lower() not in FIXTURE_SUFFIXES:
                continue
            if _is_link(path):
                findings.append(
                    f"{path.relative_to(root).as_posix()}:0: linked fixture"
                )
                continue
            fixtures.append(path)
            findings.extend(
                f"{path.relative_to(root).as_posix()}:{number}: {kind}"
                for number, kind in _private_lines(
                    path.read_text(encoding="utf-8", errors="surrogateescape")
                )
            )
    assert fixtures, "No text fixtures found for the privacy guard"
    return sorted(findings)


def test_yaml_fixtures_have_no_private_paths_or_identities():
    findings = _fixture_findings(FIXTURES)
    assert not findings, "\n".join(findings)


@pytest.mark.parametrize(
    ("path", "kinds"),
    [
        (
            BACKSLASH * 2 + BACKSLASH.join(("network", "share", "fixture.yml")),
            {"network path"},
        ),
        ("//" + "network/share/fixture.yml", {"network path"}),
        (BACKSLASH.join(("Q:", "folder", "fixture.yml")), {"drive path"}),
        ("Q:" + "/folder/fixture.yml", {"drive path"}),
        (
            BACKSLASH.join(("C:", "Users", "example", "fixture.yml")),
            {"drive path", "user-profile path"},
        ),
        ("/" + "home" + "/example/fixture.yml", {"user-profile path"}),
        ("/Users" + "/example/fixture.yml", {"user-profile path"}),
        ("ws-" + "1a", {"machine name pattern"}),
        ("DESKTOP-" + "EXAMPLE", {"machine name pattern"}),
    ],
    ids=[
        "unc",
        "network",
        "drive-backslash",
        "drive-slash",
        "profile",
        "unix",
        "mac",
        "machine",
        "desktop",
    ],
)
@pytest.mark.parametrize("prefix", ["# File: ", "includefile: ", "  - filename: "])
def test_private_comments_and_payloads_are_rejected(path, kinds, prefix):
    findings = _private_lines("---\n" + prefix + path + "\nkey: value")
    assert findings == [(2, kind) for kind in sorted(kinds)]


@pytest.mark.parametrize(
    "value",
    [
        "# Export metadata omitted for fixture privacy.",
        "# File: fixtures/template.yml",
        "# Source: https://example.invalid/reference",
        "# Ratio: a/b",
        "includefile: fixtures/template.yml",
        "source: https://example.invalid/reference",
        "ratio: a/b",
    ],
)
def test_neutral_comments_and_payloads_are_allowed(value):
    assert _private_lines(value) == []


def test_hashed_identity_tokens_are_rejected_without_disclosure(monkeypatch):
    digest = hashlib.sha256(b"synthetic-user").hexdigest()
    monkeypatch.setitem(IDENTITY_HASHES, "user name pattern", frozenset({digest}))
    assert _private_lines("# User: SYNTHETIC-USER") == [(1, "user name pattern")]
    assert _private_lines("user: synthetic-user") == [(1, "user name pattern")]
    assert _private_lines("user: synthetic-user-extra") == []


def test_scan_includes_nested_fixtures_and_redacts_diagnostics(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    for name in ("sample.yml", "sample.yaml", "sample.csv", "sample.json"):
        (nested / name).write_text(
            "\ufeff---\nincludefile: " + "Q:" + "/folder/fixture.yml\nkey: café\n",
            encoding="utf-8",
            newline="\n",
        )
    assert _fixture_findings(tmp_path) == [
        f"nested/sample{suffix}:2: drive path"
        for suffix in (".csv", ".json", ".yaml", ".yml")
    ]


def test_linked_directories_are_not_followed(tmp_path, monkeypatch):
    nested = tmp_path / "linked"
    nested.mkdir()
    (nested / "private.yml").write_text(
        "path: " + "Q:" + "/fixture.yml\n",
        encoding="utf-8",
        newline="\n",
    )
    (tmp_path / "safe.yml").write_text("key: value\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(Path, "is_junction", lambda path: path == nested, raising=False)
    assert _fixture_findings(tmp_path) == ["linked:0: linked directory"]


def test_missing_fixtures_fail_closed(tmp_path):
    with pytest.raises(AssertionError, match="No text fixtures found"):
        _fixture_findings(tmp_path)


EXPORT_FIXTURES = sorted(EXPORT_ROOT.glob("Template_*.yml")) + sorted(
    EXPORT_ROOT.glob("L0[12]*.yml")
)


def _export_payload_digests() -> tuple[str, ...]:
    actual = []
    for fixture in EXPORT_FIXTURES:
        payload = b"".join(
            line
            for line in fixture.read_bytes().splitlines(keepends=True)
            if not line.lstrip().startswith(b"#")
        )
        actual.append(hashlib.sha256(payload).hexdigest())
    return tuple(actual)


def test_export_fixture_payloads_match_sanitized_baseline():
    """Pin non-comment bytes after privacy-only substitutions to the baseline.

    Baseline: origin/main at 3626a05b71442557df44168bf2ac962dd88205c7.
    Only identifying path scalars and export comments were replaced; numeric
    data, placeholders, duplicate keys and original line endings are preserved.
    """
    expected = (
        "84c15a48df7b62998578544e341499f3023fcb37c5129e5961757c5cbfdf58c4",
        "5248a26dea22bd0b538489008f2aff7e451cf7665ac314c0160e433f0932e066",
        "9d08d0a48bfa5f24783a268cc780543eb5cae51e586d36f295e6fc13227af291",
        "92d7a7b2583db8bc911617348d314d61c6930572b79f08ae8eaa38e3385c6413",
        "7f110f8993879e013628dd7f298248c07a3fabadc1bfd0d82dfcbabdc23e80e7",
        "2a3195d2dc75622e9528cf4bb3d01b9387f56d0833e8d6c296e02942904724e1",
    )
    assert _export_payload_digests() == expected, (
        'Rebuild expected digests: python -c "import runpy; '
        "m = runpy.run_path('tests/hygiene/test_yaml_fixture_header_privacy.py'); "
        "print(m['_export_payload_digests']())\""
    )


def test_export_identity_comments_are_omitted():
    for fixture in EXPORT_FIXTURES:
        text = fixture.read_text(encoding="utf-8")
        assert not re.search(r"(?m)^# (?:File|User|Machine):", text), fixture.name
