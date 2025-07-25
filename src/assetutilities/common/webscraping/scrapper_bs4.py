# Standard library imports
import os  # noqa
from io import BytesIO  # noqa

import pandas as pd
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style
from colorama import init as colorama_init

colorama_init()


class BS4Scraper:
    def __init__(self):
        pass

    def router(self, cfg):
        self.input_data(cfg)
        return cfg

    def input_data(self, cfg):
        input_settings = cfg["input_settings"]
        for input_item in cfg["input"]:
            input_item = {**input_settings, **input_item}
            self.get_data(cfg, input_item)

    def get_data(self, cfg, input_item):
        url = input_item["url"]

        session = requests.Session()

        response = session.get(url)  # GET request to the form page
        soup = BeautifulSoup(response.content, "html.parser")

        viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
        eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
        viewstate_generator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})[
            "value"
        ]

        first_request_data = cfg["form_data"]["first_request"]
        first_request_data.update(
            {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstate_generator,
                "__EVENTVALIDATION": eventvalidation,
            }
        )

        # Submit the API form
        response = session.post(url, data=first_request_data)
        soup = BeautifulSoup(response.content, "html.parser")

        if response.status_code == 200:
            print(
                f"{Fore.GREEN} submitted given form data successfully!{Style.RESET_ALL}"
            )
        else:
            print(
                f"{Fore.RED}Failed to submit the form data {Style.RESET_ALL}. Status code: {response.status_code}"
            )

        viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
        eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
        viewstate_generator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})[
            "value"
        ]

        second_request_data = cfg["form_data"]["second_request"]
        second_request_data.update(
            {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstate_generator,
                "__EVENTVALIDATION": eventvalidation,
            }
        )

        csv_response = session.post(url, data=second_request_data)

        label = input_item["label"]
        output_path = input_item["output_dir"]
        csv_path = os.path.join(output_path, f"{label}.csv")

        if csv_response.status_code == 200:
            with open(csv_path, "wb") as f:
                f.write(csv_response.content)
                df = pd.read_csv(
                    BytesIO(csv_response.content)
                )  # class <bytes> to pandas df
                print()
                print("****The Scraped data of given parameter ****\n\n")
                print(df)
        else:
            print(
                f"{Fore.RED}Failed to export CSV file.{Style.RESET_ALL} Status code: {csv_response.status_code}"
            )
