"""Behaviour of the deepdiff call sites under deepdiff 8.x.

deepdiff 8 inserted ``_original_type`` as the third positional parameter of
``DeepDiff``, so options passed positionally land on the wrong parameters.
These tests pin the options the helpers intend to apply.
"""

from pathlib import Path

import pytest
import yaml
from deepdiff import DeepDiff

from assetutilities.common.pytest_utilities import pytest_deepdiff_nested_dict
from assetutilities.common.yml_utilities import WorkingWithYAML


def test_nested_dict_equal_inputs_pass():
    pytest_deepdiff_nested_dict({"a": {"b": [1, 2]}}, {"a": {"b": [1, 2]}})


def test_nested_dict_ignores_list_order():
    pytest_deepdiff_nested_dict({"a": [1, 2, 3]}, {"a": [3, 1, 2]})


def test_nested_dict_applies_significant_digits():
    pytest_deepdiff_nested_dict({"x": 1.00000001}, {"x": 1.0})


def test_nested_dict_respects_ignore_order_false():
    with pytest.raises(AssertionError):
        pytest_deepdiff_nested_dict({"a": [1, 2]}, {"a": [2, 1]}, ignore_order=False)


def test_nested_dict_reports_real_difference():
    with pytest.raises(AssertionError):
        pytest_deepdiff_nested_dict({"a": 1}, {"a": 2})


def test_save_diff_files_writes_changed_values(tmp_path: Path):
    first = {"depth": 100, "name": "riser", "items": [1, 2]}
    second = {"depth": 120, "name": "riser", "items": [2, 1], "added": True}
    file_name1 = tmp_path / "case_a.yml"
    file_name2 = tmp_path / "case_b.yml"
    file_name1.write_text(yaml.safe_dump(first))
    file_name2.write_text(yaml.safe_dump(second))

    file_diff = DeepDiff(first, second, ignore_order=True)
    assert set(file_diff) == {"values_changed", "dictionary_item_added"}

    cfg = {"file_name1": str(file_name1), "file_name2": str(file_name2)}
    WorkingWithYAML().save_diff_files(file_diff, cfg)

    updated = list(tmp_path.glob("wwyaml_*_updated_values.yml"))
    assert len(updated) == 1
    assert updated[0].read_text().strip() == "root['depth']: 120"

    values_changed = list(tmp_path.glob("wwyaml_*_values_changed.yml"))
    assert len(values_changed) == 1
    assert yaml.safe_load(values_changed[0].read_text()) == {
        "root['depth']": {"new_value": 120, "old_value": 100}
    }

    assert len(list(tmp_path.glob("wwyaml_*_items.yml"))) == 1
