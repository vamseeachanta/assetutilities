"""Exercise actual pytest selection without making any external requests."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "marker,expected",
    [(None, "test_unit"), ("live_data", "test_live"), ("pdf_integration", "test_pdf")],
)
def test_default_and_explicit_marker_selection(tmp_path, marker, expected):
    path = tmp_path / "test_selection.py"
    path.write_text(
        "import pytest\n"
        "def test_unit(): pass\n"
        "@pytest.mark.live_data\ndef test_live(): pass\n"
        "@pytest.mark.pdf_integration\ndef test_pdf(): pass\n"
    )
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        str(ROOT / "pytest.ini"),
        str(path),
        "--collect-only",
        "-q",
        "-p",
        "no:cacheprovider",
    ]
    if marker:
        command.extend(["-m", marker])
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    selected = [
        line.strip() for line in result.stdout.splitlines() if "<Function" in line
    ]
    assert selected == [f"<Function {expected}>"]
