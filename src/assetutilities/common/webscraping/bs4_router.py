from assetutilities.common.webscraping.scrapper_bs4 import BS4Scrapper

bs4_scraper = BS4Scrapper()

class BS4Router:

    def __init__(self):
        pass

    def router(self, cfg):

        if "source" in cfg['scrape_data'] and  cfg['scrape_data']['source']=='loopnet':
            bs4_scraper.router(cfg)
        return cfg
