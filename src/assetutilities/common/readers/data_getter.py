# ABOUTME: File download utilities for retrieving data from URLs.
# ABOUTME: Extracted from common/data.py GetData class.
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class GetData:
    def download_file_from_url(self, cfg: dict[str, Any]) -> dict[str, Any]:
        import time

        import wget  # type: ignore[import-not-found]

        {
            "url": "https://www.data.bsee.gov/Well/Files/APIRawData.zip",
            "download_to": os.path.abspath(Path("../data_manager/data/bsee")),
        }

        url = cfg["url"]
        filename = os.path.join(cfg["download_to"] + "/" + os.path.basename(url))

        if os.path.exists(filename):
            os.remove(filename)

        start_time = time.perf_counter()
        print(f"Dowloading file: {filename}")
        wget.download(url, out=filename)
        end_time = time.perf_counter()
        print(f"Downloading file: {filename} .... COMPLETE")
        print(
            f"Time Taken to download: {(end_time - start_time).__round__(3)} .... COMPLETE"
        )
        return {"filename": filename, "result": True}
