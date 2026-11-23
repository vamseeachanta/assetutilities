# ABOUTME: Security regression tests for cli_parser legacy-dict parsing (issue #80).
# ABOUTME: Verifies ast.literal_eval safely parses valid dict literals and rejects code injection.

import sys

import pytest

# Importing assetutilities.common triggers its package __init__, which pulls in
# optional heavy deps (e.g. plotly) via validation.py. Those are unrelated to the
# code under test here; skip cleanly if the environment lacks them rather than
# failing collection.
try:
    from assetutilities.common.cli_parser import parse_hybrid_arguments
except ModuleNotFoundError as exc:  # pragma: no cover - env-dependent
    pytest.skip(
        f"assetutilities.common optional dependency missing: {exc}",
        allow_module_level=True,
    )


@pytest.fixture
def real_config(tmp_path):
    # Valid-input cases reach the final os.path.isfile(inputfile) check, so the
    # config file must actually exist on disk.
    p = tmp_path / "config.yml"
    p.write_text("placeholder: true\n")
    return str(p)


def _set_argv(monkeypatch, inputfile, arg2):
    # argv[0] must look like pytest so parse_hybrid_arguments takes the
    # is_pytest branch (uses the provided inputfile and still parses argv[2]
    # as the legacy config dict) instead of raising "2 input files".
    monkeypatch.setattr(sys, "argv", ["/usr/bin/pytest", inputfile, arg2])


class TestLegacyDictParsingIsSafe:
    def test_valid_dict_literal_parses(self, monkeypatch, real_config):
        _set_argv(monkeypatch, real_config, "{'key': 'value', 'n': 3}")
        _inputfile, cfg = parse_hybrid_arguments(inputfile=real_config)
        assert cfg == {"key": "value", "n": 3}

    def test_nested_literal_parses(self, monkeypatch, real_config):
        _set_argv(monkeypatch, real_config, "{'a': [1, 2], 'b': {'c': True}}")
        _inputfile, cfg = parse_hybrid_arguments(inputfile=real_config)
        assert cfg == {"a": [1, 2], "b": {"c": True}}

    def test_malicious_import_is_rejected(self, monkeypatch, real_config):
        # eval() would execute this; ast.literal_eval must refuse it. The dict
        # parse happens before the file-existence check, so this raises
        # ValueError regardless of the input file.
        _set_argv(monkeypatch, real_config, "{'x': __import__('os').system('echo pwned')}")
        with pytest.raises(ValueError):
            parse_hybrid_arguments(inputfile=real_config)

    def test_function_call_payload_is_rejected(self, monkeypatch, real_config):
        _set_argv(monkeypatch, real_config, "{'x': open('/etc/passwd').read()}")
        with pytest.raises(ValueError):
            parse_hybrid_arguments(inputfile=real_config)

    def test_non_dict_literal_is_rejected(self, monkeypatch, real_config):
        # A bare set literal is valid Python but not a config dict.
        _set_argv(monkeypatch, real_config, "{1, 2, 3}")
        with pytest.raises(ValueError):
            parse_hybrid_arguments(inputfile=real_config)
