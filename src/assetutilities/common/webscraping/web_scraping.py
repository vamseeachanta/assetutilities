# Third party imports
# Reader imports
from assetutilities.common.webscraping.bs4_router import BS4Router
from assetutilities.common.webscraping.scrapper_scrapy import SpiderScrapy

ss = SpiderScrapy()
bs4_router = BS4Router()


class WebScraping:
    def __init__(self):
        pass

    def router(self, cfg):
        web_scrape_engine = cfg["web_scrape_engine"]

        if web_scrape_engine == "bs4":
            bs4_router.router(cfg)
        elif web_scrape_engine == "scrapy":
            ss.router(cfg)
        elif web_scrape_engine == "selenium":
            pass

        return cfg
