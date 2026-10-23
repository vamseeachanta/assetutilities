"""Offline regression cases for the configuration shapes in issue #121."""

from copy import deepcopy

import pytest

from assetutilities.common.webscraping.input_settings import iter_input_items


def test_defaults_explicit_settings_and_item_precedence():
    """Hand merge: legacy URL, explicit output, then item label and URL win.

    The inputs are synthetic strings, not external service data. The expected
    dictionary is written independently, following the documented overlay order.
    """
    cfg = {
        "settings_master": {"url": "default", "save_csv": True},
        "input_settings": {"output_dir": "results", "url": "explicit"},
        "input": [{"label": "sample", "url": "item"}, {"label": "other"}],
    }
    original = deepcopy(cfg)
    assert list(iter_input_items(cfg)) == [
        {"url": "item", "save_csv": True, "output_dir": "results", "label": "sample"},
        {
            "url": "explicit",
            "save_csv": True,
            "output_dir": "results",
            "label": "other",
        },
    ]
    assert cfg == original


@pytest.mark.parametrize("key", ["settings_master", "input_settings"])
def test_either_defaults_key_is_supported(key):
    assert list(iter_input_items({key: {"url": "default"}, "input": [{}]})) == [
        {"url": "default"}
    ]


def test_missing_defaults_are_optional():
    assert list(iter_input_items({"input": [{"url": "item"}]})) == [{"url": "item"}]


def test_result_does_not_share_nested_values_with_input():
    cfg = {"input_settings": {"options": {"save": True}}, "input": [{}]}
    item = next(iter_input_items(cfg))
    item["options"]["save"] = False
    assert cfg["input_settings"]["options"]["save"] is True


@pytest.mark.parametrize(
    "cfg",
    [
        {"settings_master": [], "input": []},
        {"input_settings": None, "input": []},
        {"input": {}},
        {"input": ["invalid"]},
    ],
)
def test_invalid_configuration_fails_before_scraping(cfg):
    with pytest.raises(ValueError, match="input|settings"):
        list(iter_input_items(cfg))
