# Standard library imports
import io
import os
import zipfile
from urllib.parse import urlparse

import pandas as pd
import requests


class DownloadDataFromURL:
    def __init__(self):
        pass

    def router(self, cfg):
        urls = cfg["input_data"]["urls"]

        for url in urls.values():
            self.download_and_process_zip(url, cfg)

        return cfg

    def download_and_process_zip(self, url, cfg):
        base_name = os.path.basename(urlparse(url).path).replace(".zip", "")
        r = requests.get(url)
        r.raise_for_status()  # Check if the download was successful

        z = zipfile.ZipFile(io.BytesIO(r.content))

        extracted_files = z.namelist()

        output_dir = cfg["input_data"]["out_directory"]

        for file in extracted_files:
            if file.endswith("/"):
                continue
            csv_filename = (
                f"{base_name}_{os.path.splitext(os.path.basename(file))[0]}" + ".csv"
            )
            with z.open(file) as file:
                try:
                    df = pd.read_csv(
                        file,
                        sep=",",
                        encoding="ISO-8859-1",
                        low_memory=False,
                        nrows=100,
                    )
                except Exception as e:
                    print(f"Could not read {file} as CSV: {e}")
                    continue

                df.to_csv(os.path.join(output_dir, csv_filename), index=False)
