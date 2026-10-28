# Standard library imports
import io
import os
import zipfile
from collections.abc import Mapping
from urllib.parse import urlparse

import pandas as pd
import requests


class DownloadDataFromURL:
    def __init__(self):
        pass

    def router(self, cfg):
        urls = cfg["input_data"]["urls"]

        if isinstance(urls, Mapping):
            entries = list(urls.values())
        elif isinstance(urls, list):
            entries = [
                item.get("url") if isinstance(item, Mapping) else item for item in urls
            ]
        else:
            raise ValueError("input_data.urls must be a mapping or a list")
        if any(not isinstance(url, str) or not url.strip() for url in entries):
            raise ValueError(
                "input_data.urls entries must contain nonempty URL strings"
            )

        for url in entries:
            self.download_and_process_zip(url, cfg)

        return cfg

    def download_and_process_zip(self, url, cfg):
        base_name = os.path.basename(urlparse(url).path).replace(".zip", "")
        # (connect, read) timeout so a slow/hung remote cannot stall the
        # process indefinitely (review 2026-05-23).
        r = requests.get(url, timeout=(5, 30))
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
