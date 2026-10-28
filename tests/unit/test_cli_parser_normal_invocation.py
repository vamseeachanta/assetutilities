# ABOUTME: Exercise normal legacy CLI invocation directly from parser source.
# ABOUTME: Isolated children check literal types and rejection side effects.

import os
from pathlib import Path
import subprocess
import sys

import pytest


PARSER_SOURCE = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "assetutilities"
    / "common"
    / "cli_parser.py"
)

# Fixture values reproduce the independently specified nested example in
# tests/unit/test_cli_parser_security.py::TestLegacyDictParsingIsSafe.
# The set example there supplies the non-dictionary values as well.
CHILD_CHECK = r"""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys


def check():
    _, source, case = sys.argv
    assert "PYTHONPATH" not in os.environ
    spec = importlib.util.spec_from_file_location("parser_source_under_test", source)
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    assert not any(
        name == "assetutilities" or name.startswith("assetutilities.")
        for name in sys.modules
    )

    config = Path("config.yml")
    original_config = b"placeholder: true\n"
    config.write_bytes(original_config)
    marker = Path("marker")
    assert not marker.exists()
    literals = {
        "nested": "{'a': [1, 2], 'b': {'c': True}}",
        "set": "{1, 2, 3}",
        "function-call": "{'x': open('marker', 'w').write('synthetic')}",
        "import-expression": (
            "{'x': __import__('pathlib').Path('marker').write_text('synthetic')}"
        ),
    }
    original_argv = ["entry.py", "config.yml", literals[case]]
    sys.argv = original_argv.copy()
    if case == "nested":
        inputfile, cfg = parser.parse_hybrid_arguments()
        assert type(inputfile) is str
        assert inputfile == "config.yml"
        assert type(cfg) is dict
        assert cfg == {"a": [1, 2], "b": {"c": True}}
        assert all(type(key) is str for key in cfg)
        assert type(cfg["a"]) is list
        first, second = cfg["a"]
        assert type(first) is int
        assert type(second) is int
        assert type(cfg["b"]) is dict
        assert all(type(key) is str for key in cfg["b"])
        assert type(cfg["b"]["c"]) is bool
        assert cfg["b"]["c"] is True
    else:
        try:
            parser.parse_hybrid_arguments()
        except ValueError:
            pass
        else:
            raise AssertionError

    assert sys.argv == original_argv
    assert config.read_bytes() == original_config
    assert not marker.exists()


# Parser exceptions can contain supplied tokens; discard all dynamic output.
# Only fixed diagnostics cross the child boundary, including unexpected errors.
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        check()
except BaseException:
    print("FAIL")
    raise SystemExit(os.EX_SOFTWARE)
print("PASS")
"""


def _run_source_check(tmp_path, case):
    # pytest's base temporary directory is outside the checkout in this suite.
    assert PARSER_SOURCE.parent.parent.parent.parent not in tmp_path.resolve().parents
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", CHILD_CHECK, str(PARSER_SOURCE), case],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != os.EX_OK or result.stdout != "PASS\n" or result.stderr:
        pytest.fail("Parser source child check failed", pytrace=False)


def test_normal_invocation_selects_config_and_parses_nested_literal(tmp_path):
    _run_source_check(tmp_path, "nested")


@pytest.mark.parametrize("case", ["set", "function-call", "import-expression"])
def test_normal_invocation_rejects_nonliteral_or_nondict_input_without_side_effects(
    tmp_path, case
):
    _run_source_check(tmp_path, case)
