"""Selection contract from issue #99; no external services are contacted."""

import ast
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
LIVE_TESTS = (
    "tests/modules/web_scraping/test_BeautifulSoup.py",
    "tests/modules/web_scraping/test_scrapy.py",
    "tests/modules/download_data/test_dwnld_from_zipurl.py",
)


@pytest.mark.parametrize("path", LIVE_TESTS)
def test_network_entry_point_is_explicitly_marked(path):
    tree = ast.parse((ROOT / path).read_text())
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "test_run_process"
    )
    assert "pytest.mark.live_data" in {
        ast.unparse(decorator) for decorator in function.decorator_list
    }


@pytest.mark.parametrize(
    ("selection", "expected"),
    [(None, "offline"), ("live_data", "live"), ("pdf_integration", "pdf")],
)
def test_default_and_explicit_selection(tmp_path, selection, expected):
    """Hand-derived sets: default={offline}, live={live}, pdf={pdf}."""
    example = tmp_path / "test_selection.py"
    example.write_text(
        "import pytest\n"
        "def test_offline(): pass\n"
        "@pytest.mark.live_data\n"
        "def test_live(): pass\n"
        "@pytest.mark.pdf_integration\n"
        "def test_pdf(): pass\n"
    )
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        str(ROOT / "pytest.ini"),
        str(example),
        "--noconftest",
        "--collect-only",
        "-q",
        "-q",
        "-p",
        "no:cacheprovider",
    ]
    if selection is not None:
        command.extend(["-m", selection])
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "PYTEST_ADDOPTS"):
        env.pop(key, None)
    result = subprocess.run(
        command,
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for name in ("offline", "live", "pdf"):
        assert (f"::test_{name}" in result.stdout) == (name == expected)


def test_network_quarantine_is_retired():
    entries = [
        line
        for line in (ROOT / "scripts/ci/quarantine.txt").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    retired = {
        f"{prefix}{path.removeprefix('tests/')}::test_run_process"
        for path in LIVE_TESTS
        for prefix in ("tests/", "")
    }
    assert retired.isdisjoint(entries)
