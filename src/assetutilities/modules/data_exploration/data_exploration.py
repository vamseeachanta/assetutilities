# Standard library imports
import copy
import datetime
import os

# Third party imports
import pandas as pd
from loguru import logger
from pandas.api.types import is_numeric_dtype, is_string_dtype

# Reader imports
from assetutilities.common.data import ReadData
from assetutilities.common.data_management import DataManagement
from assetutilities.common.update_deep import update_deep_dictionary

read_data = ReadData()
dm = DataManagement()

df_statistics_columns = [
    "column",
    "data_type",
    "min",
    "max",
    "mean",
    "stdev",
    "start_value",
    "end_value",
    "row_count",
    "no_of_unique_values",
    "row_count_per_unique_values",
    "unique_values",
]


class DataExploration:
    def __init__(self) -> None:
        pass

    def router(self, cfg):
        logger.info(f"Starting {cfg['basename']} application ...")

        cfg = self.get_cfg_with_master_data(cfg)

        if cfg["type"]["df_statistics"]["flag"]:
            if cfg["type"]["df_statistics"]["df_array"]:
                self.get_df_array_statistics_summary(cfg)

        elif cfg["type"]["df_basic_statistics"]["flag"]:
            self.get_df_array_with_basic_statistics(cfg)
        else:
            logger.info("No data exploration type selected.")

        return cfg

    def get_df_array_statistics_summary(self, cfg, df_array=None):
        if df_array is None:
            df_array = dm.get_df_data(cfg)

        df_statistics_summary = {}

        for column in df_statistics_columns:
            df_statistics_summary.update({column: pd.DataFrame()})

        for df_item in df_array:
            label = next(iter(df_item.keys()))
            df = df_item.get(label, pd.DataFrame())
            df_statistics = self.get_df_statistics(df)

            for column in df_statistics_columns:
                df_statistics_summary[column][label] = df_statistics[column].tolist()

        df_statistics_summary_columns = self.get_df_statistics_summary_columns(
            df_statistics_summary
        )

        for column in df_statistics_columns:
            filename = os.path.join(
                cfg["Analysis"]["result_folder"],
                cfg["Analysis"]["file_name"] + "_" + column + ".csv",
            )
            df = df_statistics_summary[column]
            df.to_csv(filename, index=False)

            df_T = df.copy()
            df_T = df_T.T.copy()
            df_T.columns = df_statistics_summary_columns
            df_T["input_file"] = list(df.columns)
            filename = os.path.join(
                cfg["Analysis"]["result_folder"],
                cfg["Analysis"]["file_name"] + "_" + column + "_T.csv",
            )
            df_T.to_csv(filename, index=False)

    def get_df_array_with_basic_statistics(self, cfg):
        df_array = dm.get_df_data(cfg)
        cfg_df_basic_statistics = cfg["type"]["df_basic_statistics"]

        basic_statistic_array = []
        for df_item in df_array:
            label = next(iter(df_item.keys()))
            df = df_item.get(label, pd.DataFrame())
            df_statistics = self.get_df_with_basic_statistics(
                cfg_df_basic_statistics, df
            )
            filename = os.path.join(
                cfg["Analysis"]["result_folder"],
                cfg["Analysis"]["file_name"] + "_" + label + ".csv",
            )

            df_statistics.to_csv(filename, index=False)

            basic_statistic_array.append({"data": filename, "label": label})

        cfg[cfg["basename"]] = {
            "df_basic_statistics": {"groups": basic_statistic_array}
        }

    def get_df_with_basic_statistics(self, cfg_df_basic_statistics, df):
        df_column_data_types = self.get_inferred_df_data_types(df)
        df_columns = list(df.columns)

        df_statistics = pd.DataFrame(columns=df_columns)

        df_col_min_list = []
        df_col_max_list = []
        df_col_mean_list = []
        df_col_stdev_list = []

        for column_index, column in enumerate(df_columns):
            data_type = df_column_data_types[column_index]
            if data_type == "datetime":
                df[column] = pd.to_datetime(df[column])

            if data_type in ["numeric", "datetime"]:
                df_col_min = df[column].min()
                df_col_max = df[column].max()
                df_col_mean = df[column].mean()
                df_col_stdev = df[column].std()
            else:
                df_col_min = None
                df_col_max = None
                df_col_mean = None
                df_col_stdev = None

            df_col_min_list.append(df_col_min)
            df_col_max_list.append(df_col_max)
            df_col_mean_list.append(df_col_mean)
            df_col_stdev_list.append(df_col_stdev)

        df_statistics.loc["min"] = df_col_min_list
        df_statistics.loc["max"] = df_col_max_list
        df_statistics.loc["mean"] = df_col_mean_list
        df_statistics.loc["stdev"] = df_col_stdev_list

        df_statistics["statistic"] = df_statistics.index

        if cfg_df_basic_statistics is not None and cfg_df_basic_statistics["add_to_df"]:
            df = pd.concat([df, df_statistics])
            return df
        else:
            return df_statistics

    def get_df_statistics_summary_columns(self, df_statistics_summary):
        column_df = df_statistics_summary["column"]
        df_statistics_summary_columns = []
        for i in range(0, len(column_df)):
            unique_columns = list(set(column_df.iloc[i]))
            if len(unique_columns) > 1:
                logger.info(f"Column mismatch: {unique_columns}")
                column = ",".join(unique_columns)
            else:
                column = unique_columns[0]
            df_statistics_summary_columns.append(column)

        return df_statistics_summary_columns

    def get_inferred_df_data_types(self, df):
        df_columns = list(df.columns)
        df_column_data_types = []
        for column in df_columns:
            logger.debug(f"Data type for '{column}' : {type(df[column].iloc[0])}")
            logger.debug(f"First element for '{column}': {df[column].iloc[0]}")

            column_data_type = None
            if is_numeric_dtype(df[column]):
                column_data_type = "numeric"

            if is_string_dtype(df[column]):
                column_data_type = "string"

            if column_data_type == "string":
                try:
                    pd.to_datetime(df[column].iloc[0])
                    column_data_type = "datetime"
                except:
                    pass

            if isinstance(df[column].iloc[0], datetime.datetime) or isinstance(
                df[column].iloc[0], datetime.date
            ):
                column_data_type = "datetime"

            df_column_data_types.append(column_data_type)
            logging.debug(f"Data type array is :{df_column_data_types}")

        return df_column_data_types

    def get_df_statistics(self, df):
        df_statistics = pd.DataFrame(columns=df_statistics_columns)
        df_column_data_types = self.get_inferred_df_data_types(df)
        df_columns = list(df.columns)
        column_index = 0
        for column in df_columns:
            df_column = column
            data_type = df_column_data_types[column_index]
            row_count = len(df)
            if data_type == "datetime":
                df[column] = pd.to_datetime(df[column])

            if data_type in ["numeric", "datetime"]:
                df_col_min = df[column].min()
                df_col_max = df[column].max()
                df_col_mean = df[column].mean()
                df_col_stdev = df[column].std()
            else:
                df_col_min = None
                df_col_max = None
                df_col_mean = None
                df_col_stdev = None

            unique_values = df[column].unique()
            no_of_unique_values = len(unique_values)
            row_count_per_unique_values = row_count / no_of_unique_values

            if no_of_unique_values > 20:
                unique_values = None
            else:
                unique_values = str(unique_values)

            df_col_start_value = df[column].iloc[0]
            df_col_end_value = df[column].iloc[-1]

            output_row = [
                df_column,
                data_type,
                df_col_min,
                df_col_max,
                df_col_mean,
                df_col_stdev,
                df_col_start_value,
                df_col_end_value,
                row_count,
                no_of_unique_values,
                row_count_per_unique_values,
                unique_values,
            ]
            df_statistics.loc[len(df_statistics)] = output_row

            column_index = column_index + 1

        return df_statistics

    def get_cfg_with_master_data(self, cfg):
        if "master_settings" in cfg:
            master_settings = cfg["master_settings"].copy()
            data_settings = cfg["data"]

            for group_index in range(0, len(data_settings["groups"])):
                group = data_settings["groups"][group_index].copy()
                group = update_deep_dictionary(master_settings["groups"], group)
                data_settings["groups"][group_index] = copy.deepcopy(group)

        return cfg

    def get_filtered_df(self, data_set_cfg, df):
        df = df.copy()
        if data_set_cfg.__contains__("filter"):
            df = read_data.df_filter_by_column_values(data_set_cfg.copy(), df)
        return df.copy()
