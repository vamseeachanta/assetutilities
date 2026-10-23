"""Scraper/config integration checks; every service boundary is replaced."""

import importlib
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from assetutilities.common.update_deep import update_deep_dictionary
from assetutilities.common.webscraping.scrapper_bs4 import BS4Scraper
from assetutilities.common.webscraping.scrapper_scrapy import SpiderScrapy
from assetutilities.common.webscraping.web_scraping import WebScraping

ROOT = Path(__file__).resolve().parents[3]


def test_packaged_defaults_survive_custom_yaml_merge(monkeypatch):
    """Hand overlay: packaged URL/save flag plus custom output and label.

    Expected values come from the checked-in base YAML, not a remote service.
    Only the final HTTP operation is replaced, after actual config merging.
    """
    base = yaml.safe_load(
        (
            ROOT
            / "src/assetutilities/base_configs/modules/web_scraping/web_scraping.yml"
        ).read_text()
    )
    custom = {
        "input_settings": {"output_dir": "results"},
        "input": [{"label": "sample"}],
    }
    cfg = update_deep_dictionary(deepcopy(base), custom)
    calls = []
    monkeypatch.setattr(
        BS4Scraper, "get_data", lambda self, cfg, item: calls.append(item)
    )
    assert BS4Scraper().router(cfg) is cfg
    assert calls == [
        {**base["settings_master"], "output_dir": "results", "label": "sample"}
    ]
    SpiderScrapy().router(cfg)
    assert cfg["input"] == [{"label": "sample"}]


@pytest.mark.parametrize("engine,attribute", [("bs4", "bs4_router"), ("scrapy", "ss")])
def test_router_dispatch_offline(monkeypatch, engine, attribute):
    module = importlib.import_module("assetutilities.common.webscraping.web_scraping")
    calls = []
    monkeypatch.setattr(
        getattr(module, attribute), "router", lambda cfg: calls.append(cfg)
    )
    cfg = {"web_scrape_engine": engine}
    assert WebScraping().router(cfg) is cfg
    assert calls == [cfg]
