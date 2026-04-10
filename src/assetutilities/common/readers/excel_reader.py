# ABOUTME: Excel file reading utilities using pandas and openpyxl.
# ABOUTME: Extracted from common/data.py ReadFromExcel class.
from __future__ import annotations

from typing import Any, Union

import pandas as pd


class ReadFromExcel:
    def __init__(self) -> None:
        pass

    def from_xlsx(
        self, cfg: dict[str, Any], file_index: int = 0
    ) -> Union[pd.DataFrame, dict[str, pd.DataFrame]]:
        import pandas as pd

        if cfg.__contains__("files"):
            cfg_temp = cfg["files"]["from_xlsx"][file_index]
        else:
            cfg_temp = cfg

        if cfg_temp.__contains__("sheet_name"):
            result = pd.read_excel(
                cfg_temp["io"],
                sheet_name=cfg_temp["sheet_name"],
                skiprows=cfg_temp["skiprows"],
                skipfooter=cfg_temp["skipfooter"],
                index_col=cfg_temp["index_col"],
            )
        else:
            xls = pd.ExcelFile(cfg_temp["io"])
            result = {}
            for sheet_name in xls.sheet_names:
                result[sheet_name] = xls.parse(sheet_name)

        return result
