# ABOUTME: Core data reading utilities for Excel, PDF, ASCII, and YAML files.
# ABOUTME: Extracted from common/data.py ReadData and DefineData classes.
from __future__ import annotations

import os
from functools import reduce
from typing import Any, Optional, Union
import operator

import pandas as pd


class ReadData:
    def df_filter_by_column_values(self, cfg: dict[str, Any], df: pd.DataFrame, file_index: int = 0) -> pd.DataFrame:
        if cfg.__contains__("files"):
            filter_dict = cfg["files"]["from_xlsx"][file_index]["filter"]
        else:
            filter_dict = cfg["filter"]
        if filter_dict is not None:
            for filter_index in range(0, len(filter_dict)):
                column = filter_dict[filter_index]["column"]
                value = filter_dict[filter_index]["value"]
                df = df[df[column] == value].copy()
                df.reset_index(inplace=True, drop=True)

        return df

    def from_df_delete_unwanted_columns(self, df: pd.DataFrame, dropped_column_array: list[int]) -> pd.DataFrame:
        df.drop(df.columns[dropped_column_array], axis=1, inplace=True)

        return df

    def from_xlsx_get_line_number_containing_keyword(self, cfg: dict[str, Any]) -> Any:
        """
        https://stackoverflow.com/questions/38056233/python-search-excel-sheet-for-specific-strings-in-a-column-and-extract-those-ro/38056526
        https://www.tutorialspoint.com/How-to-check-if-multiple-strings-exist-in-another-string-in-Python
        """
        from openpyxl import load_workbook

        wb = load_workbook(cfg["io"])

        sh = wb[cfg["sheet_name"]]
        keyword_row_number = self.from_xlsx_get_WorkSheetRowNumberWithText(
            sh, cfg["key_words"]
        )
        return keyword_row_number

    def xlsx_to_df_by_keyword_search(self, cfg: dict[str, Any]) -> pd.DataFrame:
        import pandas as pd

        cfg.update(cfg["start_row"])
        row_number_with_keyword = self.from_xlsx_get_line_number_containing_keyword(cfg)
        start_row = (
            cfg["start_row"]["transform"]["scale"] * row_number_with_keyword
            + cfg["start_row"]["transform"]["shift"]
        )
        cfg.update(cfg["end_row"])
        row_number_with_keyword = self.from_xlsx_get_line_number_containing_keyword(cfg)
        end_row = (
            cfg["end_row"]["transform"]["scale"] * row_number_with_keyword
            + cfg["end_row"]["transform"]["shift"]
        )
        number_of_rows = end_row - start_row + 1
        df = pd.read_excel(
            io=cfg["io"],
            sheet_name=cfg["sheet_name"],
            skiprows=start_row - 1,
            nrows=number_of_rows,
        )
        if cfg.__contains__("column"):
            if cfg["column"].__contains__("drop_unwanted_columns"):
                dropped_column_array = list(range(len(cfg["column"]["names"]), len(df.columns)))
                df = self.from_df_delete_unwanted_columns(df, dropped_column_array)
            if cfg["column"].__contains__("names"):
                df.columns = cfg["column"]["names"]

        return df

    def superseded_xlsx_to_df_by_keyword_search(self, data: dict[str, Any]) -> pd.DataFrame:
        """
        https://stackoverflow.com/questions/38056233/python-search-excel-sheet-for-specific-strings-in-a-column-and-extract-those-ro/38056526
        https://www.tutorialspoint.com/How-to-check-if-multiple-strings-exist-in-another-string-in-Python
        """
        import pandas as pd
        import xlrd

        ReadDataRows = []
        wb = xlrd.open_workbook(data["FileName"])

        sh = wb.sheet_by_name(data["SheetName"])
        KeyWordRowNumber = self.from_xlsx_get_WorkSheetRowNumberWithText(
            sh, data["KeyWords"]
        )

        if KeyWordRowNumber is None:
            raise Exception("Error in keyword provided for search criteria")

        StartRowNumber = KeyWordRowNumber + data["RowsToSkip"]
        EndRowNumber = KeyWordRowNumber + data["RowsToSkip"] + data["RowsToRead"]
        if EndRowNumber > sh.nrows:
            EndRowNumber = sh.nrows
        for rownum in range(StartRowNumber, EndRowNumber):
            ReadDataRows.append(sh.row_values(rownum))

        df = pd.DataFrame(ReadDataRows)

        # Assign columns
        if data["Columns"] is not None:
            if data["Columns"] == "1st Row":
                df.columns = df.iloc[0]
                df.drop([0], inplace=True)
                df.reset_index(inplace=True)
            elif len(data["Columns"]) <= len(df.columns):
                AdditionalColumns = list(range(len(data["Columns"]), len(df.columns)))
                df.columns = data["Columns"] + AdditionalColumns
            else:
                df.columns = data["Columns"][0 : len(df.columns)]

        return df

    def from_xlsx_get_WorkSheetRowNumberWithText(self, sh: Any, KeyWordArray: list[str]) -> Optional[int]:
        """
        Objective: To obtain the row number of the worksheet with specified keyword(s)
        """
        rownum = None
        for rownum in range(0, sh.nrows):
            if any(keyword in sh.row_values(rownum) for keyword in KeyWordArray):
                return rownum
                break
        return None

    def read_yml_file(self, data: dict[str, Any]) -> dict[str, Any]:
        import yaml

        with open(data["io"]) as ymlfile:
            data_as_dictionary = yaml.load(ymlfile, Loader=yaml.Loader)

        return data_as_dictionary

    def extract_from_dictionary(self, data_dictionary: dict[str, Any], map_list: list[str]) -> Any:
        return reduce(operator.getitem, map_list, data_dictionary)

    def key_chain(self, data: Any, *args: Any, default: Any = None) -> Any:
        for key in args:
            if isinstance(data, dict):
                data = data.get(key, default)
            elif isinstance(data, (list, tuple)) and isinstance(key, int):
                try:
                    data = data[key]
                except IndexError:
                    return default
            else:
                return default
        return data

    def from_pdf(self, cfg: dict[str, Any], file_index: int = 0) -> Any:
        if cfg["files"]["from_pdf"][file_index].__contains__("package"):
            if cfg["files"]["from_pdf"][file_index]["package"] in [None, "tabula"]:
                df = self.from_pdf_tabula(cfg, file_index)
            elif cfg["files"]["from_pdf"][file_index]["package"] == "camelot":
                df = self.from_pdf_camelot(cfg, file_index)
        else:
            df = self.from_pdf_tabula(cfg, file_index)

        return df

    def from_pdf_tabula(self, cfg: dict[str, Any], file_index: int = 0) -> Any:
        import tabula

        df = tabula.read_pdf(
            cfg["files"]["from_pdf"][file_index]["io"],
            pages=cfg["files"]["from_pdf"][file_index]["page"],
            multiple_tables=True,
        )
        return df

    def from_pdf_camelot(self, cfg: dict[str, Any], file_index: int = 0) -> Any:
        import camelot  # type: ignore[import-not-found]

        df = camelot.read_pdf(
            cfg["files"]["from_pdf"][file_index]["io"],
            pages=cfg["files"]["from_pdf"][file_index]["page"],
            suppress_stdout=False,
        )
        print(df)
        return df

    def update_extension_of_filename(self) -> None:
        # TODO add facility to update file extension from one to another
        pass

    def from_ascii_file_get_line_number_containing_keywords(self, cfg: dict[str, Any]) -> list[int]:

        all_lines_as_strings = self.from_ascii_file_get_lines_as_string_arrays(cfg)
        keyword_line_numbers = self.get_array_rows_containing_keywords(
            all_lines_as_strings, cfg["line"]["key_words"], cfg
        )

        return keyword_line_numbers

    def get_array_rows_containing_keywords(self, array: list[Any], key_words: list[str], cfg: Optional[dict[str, Any]] = None) -> list[Any]:
        if cfg is None:
            cfg = {}
        keyword_line_numbers = []
        for rownum in range(0, len(array)):
            if any(keyword in array[rownum] for keyword in key_words):
                keyword_line_numbers.append(rownum + 1)

        cfg_transform = None
        if cfg.__contains__("line") and cfg["line"].__contains__("transform"):
            cfg_transform = cfg["line"]["transform"]
        if cfg.__contains__("transform"):
            cfg_transform = cfg["transform"]

        if cfg_transform is not None:
            keyword_line_numbers = [
                keyword_line_number * cfg_transform["scale"] + cfg_transform["shift"]
                for keyword_line_number in keyword_line_numbers
            ]

        return keyword_line_numbers

    def from_ascii_file_get_value(self, cfg: dict[str, Any]) -> Any:

        from assetutilities.common.string_utils import FromString

        from_string = FromString()
        line_text = self.from_ascii_file_get_lines_as_string_arrays(cfg)
        line_text = from_string.remove_next_line_values(line_text)
        cfg_temp = {"text": line_text}
        cfg_temp.update(cfg["filter"])
        result = from_string.get_value_by_delimiter(cfg_temp)

        return result

    def from_ascii_file_get_structured_data_delimited_white_space(self, cfg: dict[str, Any]) -> Union[pd.DataFrame, list[Any]]:
        import pandas as pd

        all_lines_as_strings = self.from_ascii_file_get_lines_as_string_arrays(cfg)
        all_lines_float_objects: list[list[Any]] = []
        for line_index in range(0, len(all_lines_as_strings)):
            if "delimiter" not in cfg or cfg["delimiter"] == "space":
                line_string_objects = all_lines_as_strings[line_index].split()
            else:
                print("Unknown delimiter")
            try:
                all_lines_float_objects.append(
                    [float(item) for item in line_string_objects]
                )
            except:
                all_lines_float_objects.append(line_string_objects)

        result: list[list[Any]] = []
        for line_float_object_index in range(0, len(all_lines_float_objects[0])):
            result.append([])

        for line_index in range(0, len(all_lines_float_objects)):
            for line_float_object_index in range(0, len(all_lines_float_objects[0])):
                result[line_float_object_index].append(
                    all_lines_float_objects[line_index][line_float_object_index]
                )

        if cfg["DataFrame"]:
            df = pd.DataFrame(columns=cfg.get("columns", None))
            for column_index in range(0, len(df.columns)):
                df[df.columns[column_index]] = result[column_index]
            result = df

        return result

    def from_ascii_file_get_lines_as_string_arrays(self, cfg: dict[str, Any]) -> list[str]:

        all_lines = []
        if isinstance(cfg["io"], list):
            from common.ETL_components import ETL_components  # type: ignore[import-not-found]

            etl_components = ETL_components(cfg=None)
            cfg["io"] = etl_components.convert_text_list_to_combined_text(cfg["io"])

        with open(cfg["io"]) as f:
            for line in f:
                all_lines.append(line)

        start_line = 1
        end_line = len(all_lines)

        if "lines_from_end" in cfg:
            end_line = len(all_lines)
            start_line = end_line - cfg["lines_from_end"]

        if isinstance(cfg.get("start_line"), (list, tuple)):
            start_line = cfg["start_line"][0]
        else:
            start_line = cfg.get("start_line", 1)

        if isinstance(cfg.get("end_line"), (list, tuple)):
            end_line = cfg["end_line"][0]
        else:
            end_line = cfg.get("end_line", len(all_lines))

        start_line = int(start_line) if start_line is not None else 1
        end_line = int(end_line) if end_line is not None else len(all_lines)

        start_line = max(start_line, 1)
        end_line = min(end_line, len(all_lines))

        if end_line is None:
            result = [all_lines[start_line - 1]]
        else:
            result = all_lines[start_line - 1 : end_line]

        return result

    def get_file_list_from_folder(
        self, folder_with_file_type: str, with_path: bool = True, with_extension: bool = True
    ) -> list[str]:

        import glob

        file_list = []
        for file in glob.glob(folder_with_file_type):
            file_list.append(file)
        if with_path:
            if with_extension:
                return file_list
            else:
                file_list = [os.path.splitext(file)[0] for file in file_list]
                return file_list
        else:
            if with_extension:
                file_list = [os.path.basename(file) for file in file_list]
                return file_list
            else:
                file_list = [
                    os.path.splitext(os.path.basename(file))[0] for file in file_list
                ]
                return file_list


class DefineData:
    def empty_data_frame(self, columns: Any = None) -> pd.DataFrame:
        import pandas as pd

        data_frame = pd.DataFrame(columns=columns)
        return data_frame

    def set_value_in_dictionary(self, data_dictionary: dict[str, Any], value: Any, map_list: Optional[list[str]] = None) -> dict[str, Any]:
        read_data = ReadData()
        # TODO Custom define maplist here
        read_data.extract_from_dictionary(data_dictionary, map_list[:-1])[
            map_list[-1]
        ] = value

        return data_dictionary
