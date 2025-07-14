import os
from pathlib import Path

from assetutilities.common.data import ReadData, SaveData

rd = ReadData()
save_data = SaveData()


class FileSplit:
    def __init__(self) -> None:
        pass

    def router(self, cfg):
        self.process_all_files(cfg)

    def process_all_files(self, cfg):
        file_extensions = cfg.file_management["files"]["files_in_current_directory"][
            "file_extensions"
        ]
        for file_ext_item in file_extensions:
            input_files = cfg["file_management"]["input_files"][file_ext_item]

            for input_file in input_files:
                self.process_split_settings(input_file, cfg)

    def process_split_settings(self, input_file, cfg):
        split_settings = cfg["split_settings"]

        for split_setting_item in split_settings:
            data = self.get_data_for_split_item(input_file, cfg, split_setting_item)
            self.save_data(data, input_file, split_setting_item["file_suffix"], cfg)

    def get_data_for_split_item(self, input_file, cfg, split_setting_item):
        line_number_cfg = split_setting_item["start"]
        start_line = self.get_line_number_by_settings(line_number_cfg, input_file)
        line_number_cfg = split_setting_item["end"]
        end_line = self.get_line_number_by_settings(line_number_cfg, input_file)

        cfg_data_format = {
            "io": input_file,
            "start_line": start_line,
            "end_line": end_line,
        }

        data = self.get_data(cfg_data_format)

        return data

    def save_data(self, data, input_file, file_suffix, cfg):
        basename = Path(input_file).stem
        if "output_directory" in cfg["Analysis"]:
            output_directory = cfg["Analysis"]["output_directory"]
        output_directory = cfg["Analysis"]["file_management_output_directory"]

        file_name = os.path.join(output_directory, basename + "_" + file_suffix)
        save_data.save_ascii_file_from_array(data, file_name)

    def get_line_number_by_settings(self, line_number_cfg, input_file):
        line_number = line_number_cfg.get("line_number", None)
        if line_number is None:
            cfg_file = {"io": input_file, "basename": os.path.basename(input_file)}
            cfg_keyword_lines = {"io": cfg_file["io"], "line": line_number_cfg}

            line_number = rd.from_ascii_file_get_line_number_containing_keywords(
                cfg_keyword_lines
            )

        return line_number

    def get_data(self, cfg_data_format):
        data = rd.from_ascii_file_get_lines_as_string_arrays(cfg_data_format)
        return data
