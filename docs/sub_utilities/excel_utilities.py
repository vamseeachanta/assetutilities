import pandas as pd
import xlwings as xw


class ExcelUtilities:
    def __init__(self) -> None:
        pass

    def read_excel(self, file_path: str, sheet_name: str) -> pd.DataFrame:
        """
        Read an excel file and return a dataframe
        """
        return pd.read_excel(file_path, sheet_name=sheet_name)

    def write_excel(self, df: pd.DataFrame, file_path: str, sheet_name: str) -> None:
        """
        Write a dataframe to an excel file
        """
        df.to_excel(file_path, sheet_name=sheet_name, index=False)

    def get_sheet_names(self, file_path: str) -> list:
        """
        Get the sheet names of an excel file
        """
        return pd.ExcelFile(file_path).sheet_names

    def get_sheet_names_dict(self, file_path: str) -> dict:
        """
        Get the sheet names of an excel file
        """
        return pd.ExcelFile(file_path).parse()

    def read_wb(self, wb_name: str) -> xw.Book:
        wb = xw.Book(wb_name)
        return wb

    def copy_and_paste_one_time(self, copy_and_paste_one_time_config):
        wb = self.read_wb(copy_and_paste_one_time_config["wb_name"])
        cp_cfg = copy_and_paste_one_time_config.copy()
        del cp_cfg["wb_name"]
        cp_cfg.update({"wb": wb})
        self.copy_and_paste_cell_range(**cp_cfg)
        wb.save()

    def copy_and_paste_cell_range(
        self,
        wb,
        source_sheet: str,
        source_range: str,
        destination_sheet: str,
        destination_range: str,
        copy_paste_type: str,
    ) -> None:
        """
        Copy and paste a cell range from one sheet to another
        """

        source = wb.sheets[source_sheet]
        destination = wb.sheets[destination_sheet]
        if copy_paste_type == "values":
            destination.range(
                destination_range["start"], destination_range["end"]
            ).value = source.range(source_range["start"], source_range["end"]).value
        elif copy_paste_type == "formulas":
            destination.range(
                destination_range["start"], destination_range["end"]
            ).formula = source.range(source_range["start"], source_range["end"]).formula
        else:
            raise Exception("Invalid copy_paste_type")

    def copy_and_paste_cell_range_repeat(self, cp_cfg_repeat):
        """
        Copy and paste a cell range from one sheet to another multiple times
        """
        # TODO Relative formula pasting is NOT working
        wb = self.read_wb(cp_cfg_repeat["wb_name"])
        cp_cfg = cp_cfg_repeat.copy()
        del cp_cfg["wb_name"]
        del cp_cfg["repeat"]
        cp_cfg.update({"wb": wb})

        for copy_paste_index in range(0, cp_cfg_repeat["repeat"]["times"]):
            dr_start_row = (
                cp_cfg_repeat["destination_range"]["start"][0]
                + copy_paste_index * cp_cfg_repeat["repeat"]["offset"]["row"]
            )
            dr_start_column = (
                cp_cfg_repeat["destination_range"]["start"][1]
                + copy_paste_index * cp_cfg_repeat["repeat"]["offset"]["column"]
            )
            dr_end_row = (
                cp_cfg_repeat["destination_range"]["end"][0]
                + copy_paste_index * cp_cfg_repeat["repeat"]["offset"]["row"]
            )
            dr_end_column = (
                cp_cfg_repeat["destination_range"]["end"][1]
                + copy_paste_index * cp_cfg_repeat["repeat"]["offset"]["column"]
            )

            cp_cfg["destination_range"]["start"] = (dr_start_row, dr_start_column)
            cp_cfg["destination_range"]["end"] = (dr_end_row, dr_end_column)

            self.copy_and_paste_cell_range(**cp_cfg)

        wb.save()


if __name__ == "__main__":
    eu = ExcelUtilities()

    # copy_and_paste_one_time_config = {
    #     'wb_name':
    #         'C:\\Users\\ss7a2365\\Documents\\github\\energy\\py\\utilities\\config.xlsx',
    #     'source_sheet':
    #         'config1',
    #     'source_range': {
    #         'start': (1, 1),    # Definition is Rows, columns
    #         'end': (6, 8)
    #     },
    #     'destination_sheet':
    #         'config2',
    #     'destination_range': {
    #         'start': (1, 1),
    #         'end': (6, 8)
    #     },
    #     'copy_paste_type':
    #         'formulas'
    # }
    # eu.copy_and_paste_one_time(copy_and_paste_one_time_config)

    copy_and_paste_config_repeat = {
        "wb_name": "C:\\Users\\ss7a2365\\Desktop\\expt.xlsx",
        "source_sheet": "Post-processing - Dynamic",
        "source_range": {"start": (32, 1), "end": (58, 9)},
        "destination_sheet": "Post-processing - Dynamic",
        "destination_range": {"start": (59, 1), "end": (85, 9)},
        "copy_paste_type": "formulas",
        "repeat": {"times": 10, "offset": {"row": 27, "column": 0}},
    }
    eu.copy_and_paste_cell_range_repeat(copy_and_paste_config_repeat)
