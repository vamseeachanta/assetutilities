from assetutilities.common.webscraping.loopnet_scraper import LoopNetScraper

loop_net_scraper = LoopNetScraper()


class BS4Router:
    def __init__(self):
        pass

    def router(self, cfg):
        if "source" in cfg["scrape_data"] and cfg["scrape_data"]["source"] == "loopnet":
            loop_net_scraper.scrape()
        return cfg
