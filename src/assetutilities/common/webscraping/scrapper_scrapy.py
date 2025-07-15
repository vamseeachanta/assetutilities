# Third party imports
import pandas as pd  # noqa
import scrapy
from scrapy import FormRequest

# from scrapy.crawler import CrawlerProcess
from scrapy.utils.response import (  # noqa useful while program is running
    open_in_browser,
)
import os  # noqa
from io import BytesIO  # noqa
import logging  # noqa

from colorama import Fore, Style
from colorama import init as colorama_init

colorama_init()

logging.getLogger("scrapy").propagate = False


class SpiderScrapy(scrapy.Spider):
    name = "API_well_data"
    start_urls = ["https://www.data.bsee.gov/Well/APD/Default.aspx"]

    def __init__(self, input_item=None, cfg=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_item = input_item
        self.cfg = cfg

    def router(self, cfg):

        # process = CrawlerProcess(settings=settings)

        input_settings = cfg["input_settings"]
        for input_item in cfg["input"]:
            input_item = {**input_settings, **input_item}
            # process.crawl(SpiderScrapy, input_item=input_item, cfg=cfg)

        # process.start()

    def parse(self, response):
        first_request_data = self.cfg["form_data"]["first_request"]

        yield FormRequest.from_response(
            response, formdata=first_request_data, callback=self.step2
        )

    def step2(self, response):
        if response.status == 200:
            print(
                f"{Fore.GREEN} submitted given form data successfully!{Style.RESET_ALL}"
            )
        else:
            print(
                f"{Fore.RED}Failed to submit the form data {Style.RESET_ALL}. Status code: {response.status}"
            )

        second_request_data = self.cfg["form_data"]["second_request"]

        yield FormRequest.from_response(
            response, formdata=second_request_data, callback=self.parse_csv_data
        )

    def parse_csv_data(self, response):
        label = self.input_item["label"]
        output_path = self.input_item["output_dir"]
        file_path = os.path.join(output_path, f"{label}.csv")

        if response.status == 200:
            with open(file_path, "wb") as f:
                f.write(response.body)
                self.scraped_data = pd.read_csv(BytesIO(response.body))
                print()
                print("\n****The Scraped data of given parameter ****\n")
                print(self.scraped_data)
        else:
            print(
                f"{Fore.RED}Failed to export CSV file.{Style.RESET_ALL} Status code: {response.status}"
            )
