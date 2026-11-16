"""Ordered set comparison with independent hand-enumerated answers."""

from pathlib import Path

import pytest
import yaml

from assetutilities.common.text_analytics import TextAnalytics


def test_comparison_preserves_first_occurrence_order(tmp_path):
    """A=[red, blue, red, green], B=[green, gold, blue, gold].

    Hand intersection in A order is [blue, green]; A minus B is [red];
    B minus A is [gold]. Unique result counts are 2, 1, 1; input sizes 4, 4.
    """
    cfg = {
        "Analysis": {"result_folder": str(tmp_path)},
        "data": {
            "set1": ["red", "blue", "red", "green"],
            "set2": ["green", "gold", "blue", "gold"],
        },
    }
    assert TextAnalytics().router(cfg) is cfg
    report = yaml.safe_load(Path(cfg["text_analytics"]["output_file"]).read_text())
    assert report == {
        "common": ["blue", "green"],
        "only_in_set1": ["red"],
        "only_in_set2": ["gold"],
        "counts": {"common": 2, "only_in_set1": 1, "only_in_set2": 1},
        "input_sizes": {"set1": 4, "set2": 4},
    }


def test_empty_sets(tmp_path):
    cfg = {
        "Analysis": {"result_folder": str(tmp_path)},
        "data": {"set1": [], "set2": []},
    }
    TextAnalytics().get_subset_files(cfg)
    assert cfg["text_analytics"]["counts"] == {
        "common": 0,
        "only_in_set1": 0,
        "only_in_set2": 0,
    }


@pytest.mark.parametrize("value", ["red", [1], [None], [["red"]]])
def test_requires_string_lists(tmp_path, value):
    cfg = {
        "Analysis": {"result_folder": str(tmp_path)},
        "data": {"set1": value, "set2": []},
    }
    with pytest.raises(ValueError, match="list of strings"):
        TextAnalytics().router(cfg)
