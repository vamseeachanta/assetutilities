# Third party imports
# Reader imports
from assetutilities.common.webscraping.scrapper_scrapy import SpiderScrapy
from assetutilities.common.webscraping.scrapper_bs4 import BS4Scrapper

ss = SpiderScrapy()
bs4 = BS4Scrapper()

class WebScraping:
    def __init__(self):
        pass

    def router(self, cfg):

        web_scrape_engine = cfg['web_scrape_engine']

        if web_scrape_engine == 'bs4':
            bs4.router(cfg)
        elif web_scrape_engine == 'scrapy':
            ss.router(cfg)
        elif web_scrape_engine == 'selenium':
            pass

