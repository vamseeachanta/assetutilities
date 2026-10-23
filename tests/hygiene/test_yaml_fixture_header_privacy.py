"""Guard text fixture comments and payloads against identifying export metadata.

Issue #132: reject local paths and export identities, allowing relative fixture
references, URLs and ratios. Diagnostics contain only file, line and kind.
"""

from __future__ import annotations

import hashlib
import os
import re
import runpy
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests"
EXAMPLES = ROOT / "examples"
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
        "mount path",
        re.compile(
            r"(?<![\w:/])/(?:mnt|media|Volumes|srv|net)(?:/|(?=$|[\s\"']))",
            re.I,
        ),
    ),
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
# Export metadata is accepted only in these neutral forms.
EXPORT_METADATA = re.compile(r"^\s*#\s*(User|Machine|File):\s*(.*?)\s*$", re.I)
METADATA_PLACEHOLDERS = {
    "user": re.compile(r"example-user"),
    "machine": re.compile(r"example-host"),
    "file": re.compile(r"fixtures/(?:[a-zA-Z0-9_-]+/)*[a-zA-Z0-9_-][a-zA-Z0-9_.-]*"),
}


def _private_lines(text: str) -> list[tuple[int, str]]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        kinds = {kind for kind, pattern in PRIVATE_PATTERNS if pattern.search(line)}
        metadata = EXPORT_METADATA.fullmatch(line)
        if metadata:
            field, value = metadata.groups()
            field = field.lower()
            if not METADATA_PLACEHOLDERS[field].fullmatch(value):
                kinds.add(f"export {field} metadata")
        findings.extend((number, kind) for kind in sorted(kinds))
    return findings


def _is_link(path: Path) -> bool:
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def _tracked_fixture_paths(root: Path) -> list[Path]:
    environment = os.environ.copy()
    for variable in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        environment.pop(variable, None)
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", root.name],
        cwd=root.parent,
        env=environment,
        check=True,
        capture_output=True,
    )
    return [
        root.parent / os.fsdecode(name) for name in result.stdout.split(b"\0") if name
    ]


def _fixture_findings(root: Path) -> list[str]:
    assert not _is_link(root), "Fixture root must not be a link"
    fixtures = []
    findings = set()
    for path in _tracked_fixture_paths(root):
        if path.suffix.lower() not in FIXTURE_SUFFIXES:
            continue
        linked_parent = next(
            (
                parent
                for parent in path.parents
                if parent != root and root in parent.parents and _is_link(parent)
            ),
            None,
        )
        if linked_parent is not None:
            findings.add(
                f"{linked_parent.relative_to(root).as_posix()}:0: linked directory"
            )
            continue
        if _is_link(path):
            findings.add(f"{path.relative_to(root).as_posix()}:0: linked fixture")
            continue
        fixtures.append(path)
        findings.update(
            f"{path.relative_to(root).as_posix()}:{number}: {kind}"
            for number, kind in _private_lines(
                path.read_text(encoding="utf-8", errors="surrogateescape")
            )
        )
    assert fixtures, "No text fixtures found for the privacy guard"
    return sorted(findings)


@pytest.mark.parametrize("root", [FIXTURES, EXAMPLES], ids=["tests", "examples"])
def test_yaml_fixtures_have_no_private_paths_or_identities(root):
    findings = _fixture_findings(root)
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
    if prefix == "# File: ":
        kinds = kinds | {"export file metadata"}
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


@pytest.mark.parametrize("field", ["User", "Machine", "File"])
@pytest.mark.parametrize("value", ["synthetic-person", "organization-node", ""])
def test_export_metadata_requires_explicit_placeholders(field, value):
    assert _private_lines(f"# {field}: {value}") == [
        (1, f"export {field.lower()} metadata")
    ]


@pytest.mark.parametrize(
    "line",
    [
        "# User: example-user",
        "# Machine: example-host",
        "# File: fixtures/reference-1.yml",
    ],
)
def test_export_metadata_placeholders_are_allowed(line):
    assert _private_lines(line) == []


@pytest.mark.parametrize("value", ["fixtures/../source.yml", "fixtures/.."])
def test_export_file_placeholders_cannot_traverse_parents(value):
    assert _private_lines(f"# File: {value}") == [(1, "export file metadata")]


def test_sibling_export_headers_use_placeholders():
    siblings = (
        FIXTURES / "modules/yml_utilities/yaml_to_plot/yml/"
        "001_ship_raos_rev2_from_aqwa_orcaflex.yml",
        FIXTURES / "modules/yml_utilities/yaml_to_plot/yml_to_plot_1/"
        "L01_import_vessels_1_vessel.yml",
    )
    for fixture in siblings:
        lines = fixture.read_text(encoding="utf-8-sig").splitlines()
        assert lines[5:7] == [
            "# User: example-user",
            "# Machine: example-host",
        ], f"{fixture.relative_to(FIXTURES).as_posix()}:6: export metadata"


def test_scan_includes_nested_fixtures_and_redacts_diagnostics(tmp_path, monkeypatch):
    monkeypatch.setitem(
        globals(), "_tracked_fixture_paths", lambda root: sorted(root.rglob("*.?*"))
    )
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


def test_scan_excludes_untracked_runtime_results(tmp_path, monkeypatch):
    root = tmp_path / "tests"
    root.mkdir()
    safe = root / "safe.yml"
    safe.write_text("key: value\n", encoding="utf-8")
    results = root / "results"
    results.mkdir()
    (results / "generated.yml").write_text(
        "path: " + "Q:" + "/runtime/output.yml\n", encoding="utf-8"
    )
    calls = []

    def tracked(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=b"tests/safe.yml\0")

    monkeypatch.setattr(subprocess, "run", tracked)
    assert _fixture_findings(root) == []
    assert calls == [["git", "ls-files", "-z", "--", "tests"]]


def test_linked_directories_are_not_followed(tmp_path, monkeypatch):
    nested = tmp_path / "linked"
    nested.mkdir()
    (nested / "private.yml").write_text(
        "path: " + "Q:" + "/fixture.yml\n",
        encoding="utf-8",
        newline="\n",
    )
    (tmp_path / "safe.yml").write_text("key: value\n", encoding="utf-8", newline="\n")
    monkeypatch.setitem(
        globals(), "_tracked_fixture_paths", lambda root: sorted(root.rglob("*.yml"))
    )
    monkeypatch.setattr(Path, "is_junction", lambda path: path == nested, raising=False)
    assert _fixture_findings(tmp_path) == ["linked:0: linked directory"]


def test_missing_fixtures_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setitem(globals(), "_tracked_fixture_paths", lambda root: [])
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
            and not re.match(rb"\s*(?:includefile|\w*MeshFileName):", line)
        )
        actual.append(hashlib.sha256(payload).hexdigest())
    return tuple(actual)


def test_export_fixture_payloads_match_sanitized_baseline():
    """Pin non-comment bytes, excluding path scalars, to the original revision.

    Original revision: 3626a05b71442557df44168bf2ac962dd88205c7.
    Digests were computed independently from that revision with git show.
    Export comments, includefile and mesh file paths are excluded; all other
    bytes, duplicate keys and original line endings are preserved.
    """
    expected = (
        "f73e3428db480bfd3c668f572568c1cc15cf5de3c91e7ae1c8a0646dfeae2182",
        "1b8a17194ff50e7dab9f366513ed323b847f8b02ca40b05935fe60f05b4dd2ac",
        "8d386f42fbfae5f33021b6e1395b23eb46303507475649540beca0cfb15015e2",
        "3a244fa86f2c6665f57e0457058d4ab7cc4761b5c13b00f23b3d09ac09bf4c69",
        "ef6e901b522f2486f01890120719327188324e77276dcd99421dab7384fd3031",
        "2a3195d2dc75622e9528cf4bb3d01b9387f56d0833e8d6c296e02942904724e1",
    )
    assert _export_payload_digests() == expected


def test_export_identity_comments_are_omitted():
    for fixture in EXPORT_FIXTURES:
        text = fixture.read_text(encoding="utf-8")
        assert not re.search(r"(?m)^# (?:File|User|Machine):", text), fixture.name


DIRECTORY_FIXTURES = (
    "modules/excel_utilities/app_excel_utilities_excel_utilities.yml",
    "modules/excel_utilities/app_excel_utilities_excel_utilities_custom_calculation.yml",
    "modules/excel_utilities/excel_utilities_cross_reference_closed_workbook.yml",
    "modules/reportgen/reportgen-cfg-20in-docx.yml",
    "modules/reportgen/reportgen-cfg-20in-md.yml",
    "modules/reportgen/reportgen-cfg-docx.yml",
    "modules/reportgen/reportgen-cfg-evolving.yml",
    "modules/reportgen/reportgen-cfg-md.yml",
    "modules/reportgen/reportgen-cfg.yml",
    "modules/reportgen/reportgen-sympy_function_1_cfg.yml",
)


@pytest.mark.parametrize("relative", DIRECTORY_FIXTURES)
def test_directory_placeholders_remain_relative_directories(relative):
    text = (FIXTURES / relative).read_text(encoding="utf-8")
    values = re.findall(
        r"^\s*(?:project_root|analysis_root_folder|log_folder|result_folder|path):"
        r"\s*[\"\']?([^\"\'\s]+)",
        text,
        re.M,
    )
    assert values
    assert all(re.fullmatch(r"fixtures/reference-\d+/", v) for v in values)


BATCH_FIXTURES = (
    "app_file_edit_file_edit_concatenate_array.bat",
    "file_edit_concatenate_2d_array_0.bat",
    "file_edit_concatenate_2d_array_1.bat",
    "file_edit_concatenate_array.bat",
    "file_edit_concatenate_array_0.bat",
    "file_edit_concatenate_array.yml",
    "file_edit_concatenate_2d_array.yml",
)


@pytest.mark.parametrize("name", BATCH_FIXTURES)
def test_batch_placeholders_keep_a_command_and_argument(name):
    text = (FIXTURES / "modules/file_edit" / name).read_text(encoding="utf-8")
    commands = (
        text.splitlines()
        if name.endswith(".bat")
        else re.findall(r"^\s*content: (.+)$", text, re.M)
    )
    assert commands
    assert all(
        re.fullmatch(r"fixture-command fixtures/reference-\d+\.dat", c)
        for c in commands
    )


@pytest.mark.parametrize("directory", ["mnt", "media", "Volumes", "srv", "net"])
@pytest.mark.parametrize("prefix", ["# File: ", "path: ", 'path: "', "path: '"])
def test_absolute_mount_paths_are_rejected(directory, prefix):
    path = "/" + directory + "/example/fixture.yml"
    kinds = {"mount path"}
    if prefix == "# File: ":
        kinds.add("export file metadata")
    assert _private_lines(prefix + path) == [(1, kind) for kind in sorted(kinds)]


@pytest.mark.parametrize(
    "value",
    [
        "path: fixtures/" + "mnt/example.yml",
        "path: /mnt-relative/example.yml",
        "source: https://example.invalid/srv/example.yml",
        "source: https://example.invalid/Volumes/example.yml",
    ],
)
def test_relative_mount_names_and_urls_are_allowed(value):
    assert _private_lines(value) == []


@pytest.mark.parametrize("directory", ["tests", "examples"])
def test_git_listing_uses_requested_root_and_clean_environment(
    tmp_path, monkeypatch, directory
):
    for variable in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.setenv(variable, str(tmp_path / "foreign"))
    monkeypatch.setenv("FIXTURE_GUARD_SENTINEL", "preserved")
    calls = []

    def tracked(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command, 0, stdout=f"{directory}/safe.yml\0".encode("utf-8")
        )

    monkeypatch.setattr(subprocess, "run", tracked)
    root = tmp_path / directory
    assert _tracked_fixture_paths(root) == [root / "safe.yml"]
    command, options = calls[0]
    assert command == ["git", "ls-files", "-z", "--", directory]
    assert options["cwd"] == tmp_path
    assert not {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"} & options["env"].keys()
    assert options["env"]["FIXTURE_GUARD_SENTINEL"] == "preserved"
    assert "GIT_DIR" in os.environ


@pytest.mark.parametrize("name", ["inputs.csv", "results.csv"])
def test_example_csv_paths_match_sanitized_test_fixtures(name):
    relative = Path("modules/excel_utilities/input_data") / name
    actual = (
        ROOT / "examples/workflows/excel_utilities/input_data" / name
    ).read_bytes()
    expected = (FIXTURES / relative).read_bytes()
    assert actual.splitlines() == expected.splitlines()
    assert b"\r" not in actual


def test_concatenate_import_does_not_run_engine(monkeypatch):
    calls = []
    module = types.ModuleType("assetutilities.engine")
    module.engine = lambda *args, **kwargs: calls.append((args, kwargs))
    monkeypatch.setitem(sys.modules, "assetutilities.engine", module)
    monkeypatch.setattr(sys, "argv", ["pytest"])
    runpy.run_path(
        str(FIXTURES / "modules/file_edit/test_file_edit_concatenate_array.py")
    )
    assert calls == []
