# Third party imports


from test_df_basic_statistics import test_run_process as test_df_basic_statistics_copy
from test_df_basic_statistics_add_to_df import (
    test_run_process as test_df_basic_statistics_add_to_df_copy,
)


def test_df_basic_statistics():
    test_df_basic_statistics_copy()


def test_df_basic_statistics_add_to_df():
    test_df_basic_statistics_add_to_df_copy()
