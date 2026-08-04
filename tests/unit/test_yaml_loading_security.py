# ABOUTME: Regression tests for YAML loading in assetutilities (issue #80).
# ABOUTME: Every config loader must use safe_load: python-tag payloads rejected, plain YAML still loads.

import pytest
import yaml

try:
    from assetutilities.common.readers.data_reader import ReadData
    from assetutilities.common.ymlInput import ymlInput as plain_yml_input
    from assetutilities.common.yml_utilities import WorkingWithYAML
except ModuleNotFoundError as exc:  # pragma: no cover - env-dependent
    pytest.skip(
        f"assetutilities.common optional dependency missing: {exc}",
        allow_module_level=True,
    )


# A payload that yaml.Loader / yaml.UnsafeLoader would happily instantiate and
# which yaml.safe_load must refuse. os.system is the canonical RCE gadget.
UNSAFE_YAML = "cmd: !!python/object/apply:os.system ['echo pwned']\n"

# The legitimate counterpart: ordinary scalars/lists/maps that safe_load has
# always supported. If a fix broke normal configs this would fail.
LEGITIMATE_YAML = (
    "basename: viz\n"
    "settings:\n"
    "  plt_kind: line\n"
    "  dpi: 800\n"
    "  flags: [true, false]\n"
)

LEGITIMATE_EXPECTED = {
    "basename": "viz",
    "settings": {"plt_kind": "line", "dpi": 800, "flags": [True, False]},
}


@pytest.fixture
def unsafe_file(tmp_path):
    p = tmp_path / "unsafe.yml"
    p.write_text(UNSAFE_YAML)
    return str(p)


@pytest.fixture
def legit_file(tmp_path):
    p = tmp_path / "legit.yml"
    p.write_text(LEGITIMATE_YAML)
    return str(p)


class TestWorkingWithYAMLymlInput:
    def test_python_tag_payload_is_rejected(self, unsafe_file):
        with pytest.raises(yaml.constructor.ConstructorError):
            WorkingWithYAML().ymlInput(unsafe_file)

    def test_legitimate_yaml_still_loads(self, legit_file):
        assert WorkingWithYAML().ymlInput(legit_file) == LEGITIMATE_EXPECTED


class TestCommonYmlInput:
    def test_python_tag_payload_is_rejected(self, unsafe_file):
        with pytest.raises(yaml.constructor.ConstructorError):
            plain_yml_input(unsafe_file, None)

    def test_legitimate_yaml_still_loads(self, legit_file):
        assert plain_yml_input(legit_file, None) == LEGITIMATE_EXPECTED


class TestDataReaderReadYmlFile:
    def test_python_tag_payload_is_rejected(self, unsafe_file):
        with pytest.raises(yaml.constructor.ConstructorError):
            ReadData().read_yml_file({"io": unsafe_file})

    def test_legitimate_yaml_still_loads(self, legit_file):
        assert ReadData().read_yml_file({"io": legit_file}) == LEGITIMATE_EXPECTED
