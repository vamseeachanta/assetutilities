"""Exercise the reusable Bash helper without contacting a package index."""

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "scripts/release/build.sh"


@pytest.fixture
def release_case(tmp_path):
    """Synthetic metadata: tag = 'v' + '1.2.3', hence expected v1.2.3."""
    project = tmp_path / "sample package"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        '[project]\nname = "sample-package"\nversion = "1.2.3"\n'
    )
    fake_uv = tmp_path / "fake uv"
    fake_uv.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, pathlib, sys\n"
        "with open(os.environ['CALLS'], 'a') as stream:\n"
        "    stream.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "if os.environ.get('FAIL_BUILD') and sys.argv[1] == 'build':\n"
        "    sys.exit(7)\n"
        "if os.environ.get('FAIL_CHECK') and sys.argv[1] == 'run':\n"
        "    sys.exit(8)\n"
        "if sys.argv[1] == 'build':\n"
        "    output = pathlib.Path(sys.argv[sys.argv.index('--out-dir') + 1])\n"
        "    (output / 'sample_package-1.2.3-py3-none-any.whl').touch()\n"
        "    (output / 'sample_package-1.2.3.tar.gz').touch()\n"
    )
    fake_uv.chmod(0o755)
    env = dict(os.environ, UV=str(fake_uv), CALLS=str(tmp_path / "calls"))
    return project, tmp_path / "fresh output", env


def run_build(case, tag="v1.2.3", **changes):
    project, output, env = case
    return subprocess.run(
        ["bash", str(BUILD), str(project), str(output), tag],
        text=True,
        capture_output=True,
        env=dict(env, **changes),
        check=False,
    )


def test_builds_then_checks_both_distributions(release_case):
    """Expect build then strict Twine validation, with no upload invocation."""
    project, output, env = release_case
    result = run_build(release_case)
    assert result.returncode == 0, result.stderr
    calls = [json.loads(line) for line in Path(env["CALLS"]).read_text().splitlines()]
    assert calls == [
        ["build", "--no-sources", "--out-dir", str(output), str(project)],
        [
            "run",
            "--no-project",
            "--with",
            "twine",
            "python",
            "-m",
            "twine",
            "check",
            "--strict",
            str(output / "sample_package-1.2.3-py3-none-any.whl"),
            str(output / "sample_package-1.2.3.tar.gz"),
        ],
    ]


@pytest.mark.parametrize("tag", ["v1.2.4", "1.2.3", "main", "v1.2.3; false"])
def test_wrong_tag_prevents_build(release_case, tag):
    assert run_build(release_case, tag).returncode != 0
    assert not Path(release_case[2]["CALLS"]).exists()
    assert not release_case[1].exists()


def test_stale_output_prevents_build_without_deleting_data(release_case):
    output = release_case[1]
    output.mkdir()
    previous = output / "previous.whl"
    previous.write_text("retained")
    assert run_build(release_case).returncode != 0
    assert previous.read_text() == "retained"
    assert not Path(release_case[2]["CALLS"]).exists()


def test_build_failure_stops_before_metadata_check(release_case):
    result = run_build(release_case, FAIL_BUILD="1")
    assert result.returncode == 7
    calls = Path(release_case[2]["CALLS"]).read_text().splitlines()
    assert len(calls) == 1


def test_missing_arguments_has_usage():
    result = subprocess.run(
        ["bash", str(BUILD)], text=True, capture_output=True, check=False
    )
    assert result.returncode != 0
    assert "Usage:" in result.stderr


def test_metadata_check_failure_is_propagated(release_case):
    """A failed strict check returns failure while retaining built artifacts."""
    result = run_build(release_case, FAIL_CHECK="1")
    assert result.returncode == 8
    assert len(list(release_case[1].glob("*.whl"))) == 1
    assert len(list(release_case[1].glob("*.tar.gz"))) == 1
    assert len(Path(release_case[2]["CALLS"]).read_text().splitlines()) == 2


def test_existing_empty_output_is_allowed(release_case):
    release_case[1].mkdir()
    result = run_build(release_case)
    assert result.returncode == 0, result.stderr
