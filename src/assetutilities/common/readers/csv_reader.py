# ABOUTME: CSV file reading utilities using pandas.
# ABOUTME: Extracted from common/data.py ReadFromCSV class.
from __future__ import annotations

from typing import Any

import pandas as pd


class ReadFromCSV:
    def __init__(self) -> None:
        pass

    def to_df(self, cfg: dict[str, Any], file_index: int = 0) -> Any:

        pd.read_csv(cfg["io"], delimiter=cfg["delimiter"], delim_whitespace=True)

        return result  # noqa: F821
