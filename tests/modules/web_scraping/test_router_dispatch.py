"""Hermetic dispatch coverage, independent of live scrape configuration."""

from types import SimpleNamespace

import pytest

import assetutilities.common.webscraping.web_scraping as web_scraping


@pytest.mark.parametrize("engine", ["bs4", "scrapy", "selenium", "unknown"])
def test_router_dispatches_only_selected_engine(monkeypatch, engine):
    """Expected calls follow the selected config string, with identity preserved."""
    calls = []
    monkeypatch.setattr(
        web_scraping,
        "bs4_router",
        SimpleNamespace(router=lambda cfg: calls.append(("bs4", cfg))),
    )
    monkeypatch.setattr(
        web_scraping,
        "ss",
        SimpleNamespace(router=lambda cfg: calls.append(("scrapy", cfg))),
    )
    cfg = {"web_scrape_engine": engine}
    assert web_scraping.WebScraping().router(cfg) is cfg
    if engine in {"bs4", "scrapy"}:
        assert calls == [(engine, cfg)]
        assert calls[0][1] is cfg
    else:
        assert calls == []
