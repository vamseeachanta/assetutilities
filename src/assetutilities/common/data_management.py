# Standard library imports
import os

# Third party imports
import pandas as pd

# Reader imports
from assetutilities.common.data import ReadData, Transform
from assetutilities.common.utilities import is_file_valid_func

read_data = ReadData()
trans = Transform()


class DataManagement:
    def __init__(self) -> None:
        pass

    def router(self, cfg):
        pass

    def get_df_data(self, cfg):
        if cfg["data"]["type"] == "file_management":
            file_list = cfg["file_management"]["input_files"]["csv"].copy()
            cfg["data"]["groups"] = [{"file_name": file} for file in file_list]

        df_array = self.get_df_array_from_cfg(cfg)

        return df_array

    def get_df_array_from_cfg(self, cfg):
        df_array = []
        for group_cfg in cfg["data"]["groups"]:
            analysis_root_folder = cfg["Analysis"]["analysis_root_folder"]
            file_is_valid, valid_file = is_file_valid_func(
                group_cfg["file_name"], analysis_root_folder
            )
            if not file_is_valid:
                raise ValueError(f"Invalid file name/path: {group_cfg['file_name']}")

            df = pd.read_csv(valid_file)
            df = self.get_filtered_df(group_cfg, df)
            label = group_cfg.get("label", None)
            if label is None:
                label = os.path.basename(group_cfg["file_name"])
            df_array.append({label: df})

        return df_array

    def get_filtered_df(self, data_set_cfg, df):
        df = df.copy()
        if data_set_cfg.__contains__("filter"):
            df = read_data.df_filter_by_column_values(data_set_cfg.copy(), df)
        return df.copy()

    def get_transformed_df(self, data_set_cfg, df):
        df = df.copy()
        if data_set_cfg.__contains__("transform"):
            df = trans.get_transformed_df(data_set_cfg["transform"].copy(), df)

        return df.copy()
