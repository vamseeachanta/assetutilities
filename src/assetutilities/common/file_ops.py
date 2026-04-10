# ABOUTME: File copy/paste and Excel-to-Word transfer operations.
# ABOUTME: Extracted from common/data.py CopyAndPasteFiles and TransferDataFromExcelToWord classes.
from __future__ import annotations

from typing import Any, Optional


class TransferDataFromExcelToWord:
    def __init__(self) -> None:
        pass

    def transfer_table_from_excel_to_word(self, cfg: Optional[dict[str, Any]] = None) -> None:
        if cfg is None:
            cfg = {
                "excel_file": "K:\\0173 KM Extreme\\SLWR\\Fatigue\\Test.xlsx",
                "sheet_name": "Sheet1",
                "table_name": "Table1",
                "word_file": "K:\\0173 KM Extreme\\SLWR\\Fatigue\\Test.docx",
                "word_table_name": "Table1",
            }
        # TODO implement this function


class CopyAndPasteFiles:
    """
    Class to copy and paste files from 1 directory to another.
    """

    def __init__(self) -> None:
        pass

    def iterate_all_cfgs(self, cfgs: dict[str, Any]) -> None:
        copy_cfgs = cfgs["copy_cfgs"].copy()
        for cfg in copy_cfgs:
            self.copy_files(cfg)

    def copy_files(self, cfg: dict[str, Any]) -> None:
        """
        cfg = {
            'source_dir': 'C:\\Users\\kylem\\Desktop\\Test\\',
            'destination_dirs': 'C:\\Users\\kylem\\Desktop\\Test2\\',
            'file_names': ['test1.txt', 'test2.txt']
        }
        """
        import shutil

        file_names = cfg["files"]
        for file_name in file_names:
            for destination_dir in cfg["destination_dirs"]:
                shutil.copy(cfg["source_dir"] + file_name, destination_dir + file_name)
