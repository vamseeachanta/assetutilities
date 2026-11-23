# ABOUTME: Date and time conversion utilities for DataFrames.
# ABOUTME: Extracted from common/data.py DateTimeUtility class and transform_df_datetime_to_str.
from __future__ import annotations

import datetime
from typing import Any

import pandas as pd


class DateTimeUtility:
    def last_day_of_month(self, any_day: Any) -> Any:
        import datetime

        next_month = any_day.replace(day=28) + datetime.timedelta(
            days=4
        )  # this will never fail
        return next_month - datetime.timedelta(days=next_month.day)


def transform_df_datetime_to_str(df: pd.DataFrame, date_format: str = "%Y-%m-%d %H:%M:%S") -> pd.DataFrame:
    df = df.copy()
    if len(df) > 0:
        df_columns = list(df.columns)
        for column in df_columns:
            if isinstance(df[column].iloc[0], datetime.datetime) or isinstance(
                df[column].iloc[0], datetime.date
            ):
                df[column] = [
                    item.strftime(date_format) for item in df[column].to_list()
                ]

    return df
