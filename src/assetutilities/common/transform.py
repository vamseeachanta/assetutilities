# ABOUTME: DataFrame transformation, GIS conversion, and data format utilities.
# ABOUTME: Extracted from common/data.py Transform, TransformData, and PandasChainedAssignent classes.
from __future__ import annotations

import json
from typing import Any, Optional, Union

import numpy as np
import pandas as pd


class Transform:
    def numpy_interp(
        self,
    ) -> None:
        # TODO Add for when the x and y are in ascending or descending order to handle correct interpolation
        pass

    def gis_deg_to_distance(self, df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
        import utm

        longitude_column = cfg["Longitude"]
        latitude_column = cfg["Latitude"]
        x_array = []
        y_array = []
        zone_array = []
        ut_array = []
        for df_row in range(0, len(df)):
            try:
                latitude = float(df[latitude_column].iloc[df_row])
                longitude = float(df[longitude_column].iloc[df_row])
                x, y, zone, ut = utm.from_latlon(latitude, longitude)
            except:
                x, y, zone, ut = (None, None, None, None)
            x_array.append(x)
            y_array.append(y)
            zone_array.append(zone)
            ut_array.append(ut)

        df[cfg["label"] + "_x"] = x_array
        df[cfg["label"] + "_y"] = y_array
        df[cfg["label"] + "_zone"] = zone_array
        df[cfg["label"] + "_ut"] = ut_array
        return df

    def gis_distance_to_deg(self) -> None:
        # TODO
        pass

    def get_gis_converted_df_superseded(self, data_set_cfg: dict[str, Any], df: pd.DataFrame) -> pd.DataFrame:
        if data_set_cfg.__contains__("gis"):
            import pyproj  # type: ignore[import-not-found]

            p = pyproj.Proj(proj="utm", zone=data_set_cfg["gis"]["zone"], ellps="WGS84")
            if data_set_cfg["gis"]["long_lat_to_northing_easting"]["flag"]:
                longitude_column = data_set_cfg["gis"]["long_lat_to_northing_easting"][
                    "Longitude"
                ]
                latitude_column = data_set_cfg["gis"]["long_lat_to_northing_easting"][
                    "Latitude"
                ]
                df["Easting"], df["Northing"] = p(
                    df[longitude_column].astype(float).tolist(),
                    df[latitude_column].astype(float).tolist(),
                )
            elif data_set_cfg["gis"]["long_lat_to_x_y"]["flag"]:
                import utm

                longitude_column = data_set_cfg["gis"]["long_lat_to_x_y"]["Longitude"]
                latitude_column = data_set_cfg["gis"]["long_lat_to_x_y"]["Latitude"]
                df["x"], df["y"], zone, ut = utm.from_latlon(
                    df[longitude_column].astype(float).tolist(),
                    df[latitude_column].astype(float).tolist(),
                )
            elif data_set_cfg["gis"]["northing_easting_to_long_lat"]["flag"]:
                Easting_column = data_set_cfg["gis"]["long_lat_to_northing_easting"][
                    "Easting"
                ]
                Northing_column = data_set_cfg["gis"]["long_lat_to_northing_easting"][
                    "Northing"
                ]
                df["Longitude"], df["Latitude"] = p(
                    df[Easting_column].tolist(),
                    df[Northing_column].tolist(),
                    inverse=True,
                )

        return df

    def dataframe_to_dataframe(self, df: pd.DataFrame, cfg: Optional[dict[str, Any]] = None) -> pd.DataFrame:
        df_transposed = self.transpose_df(df, cfg)
        df_transposed = self.add_column_to_df(df_transposed, cfg)

        return df_transposed

    def dataframe_to_dict(self, df: Optional[pd.DataFrame], cfg: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if cfg is None:
            cfg = {}
        json_dict = {}
        if df is not None:
            orient = cfg.get("orient", "records")
            if len(df.columns.unique()) == len(df.columns):
                json_string = df.to_json(orient=orient)
                json_dict = json.loads(json_string)

        return json_dict

    def df_JSON_strings_values_to_dict(self, df: Optional[pd.DataFrame], cfg_settings: dict[str, Any]) -> Optional[pd.DataFrame]:
        if df is not None:
            if cfg_settings.__contains__("json_transformation"):
                for column in cfg_settings["json_transformation"]["columns"]:
                    json_array = []
                    for df_row in range(0, len(df)):
                        json_array.append(json.loads(df.iloc[df_row][column]))
                    df[column] = json_array

        return df.copy() if df is not None else None

    def dataframe_to_json(self, df: Optional[pd.DataFrame], cfg: Optional[dict[str, Any]] = None) -> Union[str, dict[str, Any]]:
        import pandas as pd

        if cfg is None:
            cfg = {}
        json_string = ""
        if df is not None:
            orient = cfg.get("orient", "records")
            index = cfg.get("index", True)
            if index:
                df.insert(0, column="   ", value=list(df.index))

            if len(df.columns.unique()) == len(df.columns):
                json_string = df.apply(lambda x: pd.Series(x.dropna()), axis=1).to_json(
                    orient=orient
                )
            else:
                df = self.df_transform_repeat_columns_to_unique_columns(df)
                json_string = df.to_json(orient=orient)
        return json_string

    def df_transform_repeat_columns_to_unique_columns(
        self, df: pd.DataFrame, transform_character: str = "trailing_alphabet"
    ) -> pd.DataFrame:
        old_columns = list(df.columns)
        cfg = {"list": old_columns, "transform_character": transform_character}
        new_columns = self.transform_list_to_unique_list(cfg)
        df.columns = new_columns
        return df

    def transform_list_to_unique_list(self, cfg: dict[str, Any]) -> list[str]:
        old_list = cfg["list"]
        old_list.reverse()
        new_list = old_list.copy()
        transform_character = cfg["transform_character"]
        for list_index in range(0, len(old_list)):
            list_element = old_list[list_index]
            repeat_element_count = new_list.count(list_element)
            if repeat_element_count == 1:
                pass
            elif repeat_element_count > 1:
                if transform_character == "trailing_space":
                    new_list[list_index] = new_list[list_index] + " " * (
                        repeat_element_count - 1
                    )
                elif transform_character == "leading_space":
                    new_list[list_index] = (
                        " " * (repeat_element_count - 1) + new_list[list_index]
                    )
                elif transform_character == "leading_alphabet":
                    new_list[list_index] = (
                        "a" * (repeat_element_count - 1) + new_list[list_index]
                    )
                elif transform_character == "trailing_alphabet":
                    new_list[list_index] = new_list[list_index] + "a" * (
                        repeat_element_count - 1
                    )

        new_list.reverse()
        return new_list

    def add_column_to_df(self, df: Optional[pd.DataFrame], cfg: Optional[dict[str, Any]]) -> Optional[pd.DataFrame]:
        if df is not None and cfg is not None:
            add_column_to_transposed_df = cfg.get("add_column_to_transposed_df", None)
            if add_column_to_transposed_df is not None:
                location = add_column_to_transposed_df["location"]
                header = add_column_to_transposed_df["header"]
                values = add_column_to_transposed_df["values"]
                df.insert(loc=location, column=header, value=values)

        return df

    def transpose_df(self, df: Optional[pd.DataFrame], cfg: Optional[dict[str, Any]]) -> Optional[pd.DataFrame]:
        df_transposed = df
        if df is not None and cfg is not None:
            transposed_df_column_name = cfg.get("transposed_df_column_name", None)
            if transposed_df_column_name is not None:
                transpose_df_columns = df[transposed_df_column_name["column"]].tolist()
                if transposed_df_column_name["drop"]:
                    df.drop(transposed_df_column_name["column"], axis=1, inplace=True)
                df_transposed = df.T.copy()
                df_transposed.columns = transpose_df_columns
        return df_transposed

    def dataframe_to_html(self, df: Optional[pd.DataFrame] = None, cfg_settings: Optional[dict[str, Any]] = None) -> Union[str, dict[str, Any]]:
        if cfg_settings is None:
            cfg_settings = {}
        if df is None:
            import pandas as pd

            df = pd.DataFrame(
                {
                    "name": ["Somu", "Kiku", "Amol", "Lini"],
                    "physics": [68, 74, 77, 78],
                    "chemistry": [84, 56, 73, 69],
                    "algebra": [78, 88, 82, 87],
                }
            )
        index = cfg_settings.get("index", True)
        justify = cfg_settings.get("justify", "center")
        classes = cfg_settings.get(
            "classes",
            "table table-bordered table-responsive-sm table-sm table-striped table-condensed",
        )
        max_cols = cfg_settings.get("max_cols", None)

        if (not cfg_settings.__contains__("json_transformation")) or (
            cfg_settings["json_transformation"] is None
        ):
            html = df.to_html(
                index=index, justify=justify, classes=classes, max_cols=max_cols
            )
            thead = cfg_settings.get("thead", '<thead class="thead-light">')
            html = html.replace("<thead>", thead)
            return html
        else:
            for column in cfg_settings["json_transformation"]["columns"]:
                json_array = []
                for df_row in range(0, len(df)):
                    import pandas as pd

                    try:
                        temp_df = pd.DataFrame.from_dict(
                            df.iloc[df_row][column], orient="columns"
                        )
                    except:
                        temp_df = pd.DataFrame.from_dict(
                            df.iloc[df_row][column], orient="index"
                        )
                    html = self.dataframe_to_html(temp_df)
                    json_array.append(html)
                df[column] = json_array

            df_dict = self.dataframe_to_dict(df)
            return df_dict

    def convert_numpy_types_to_native_python_types(self, cfg: dict[str, Any]) -> Optional[dict[str, Any]]:
        if cfg["datatype"] is dict:
            for key in cfg["data"].keys():
                if type(cfg["data"][key]) not in [str, int, float]:
                    cfg["data"].update({key: cfg["data"][key].item()})
            return cfg["data"]
        else:
            print("data types not supported")
        return None

    def get_transformed_df(self, cfg_transform: list[dict[str, Any]], df: pd.DataFrame) -> pd.DataFrame:
        transformed_df = df.copy()
        df_columns = list(df.columns)
        for transform_item in cfg_transform:
            column = transform_item["column"]
            if column in df_columns:
                scale = transform_item["scale"]
                shift = transform_item["shift"]
                data = list(transformed_df[column])
                transformed_df[column] = [item * scale + shift for item in data]

        return transformed_df


class TransformData:
    def __init__(self) -> None:
        pass

    def get_transformed_data(self, cfg: dict[str, Any]) -> None:
        calculate_function = getattr(self, cfg["type"])
        calculate_function(cfg)

    def linear(self, cfg: dict[str, Any]) -> dict[str, Any]:

        scale = cfg["scale"]
        shift = cfg["shift"]
        if type(cfg["data"]) is list:
            cfg["data"] = [item * scale + shift for item in cfg["data"]]
        else:
            cfg["data"] = cfg["data"] * scale + shift

        return cfg


class PandasChainedAssignent:
    def __init__(self, chained: Optional[str] = None) -> None:
        acceptable = [None, "warn", "raise"]
        assert chained in acceptable, "chained must be in " + str(acceptable)
        self.swcw = chained

    def __enter__(self) -> "PandasChainedAssignent":
        import pandas as pd

        self.saved_swcw = pd.options.mode.chained_assignment
        pd.options.mode.chained_assignment = self.swcw
        return self

    def __exit__(self, *args: Any) -> None:
        import pandas as pd

        pd.options.mode.chained_assignment = self.saved_swcw
