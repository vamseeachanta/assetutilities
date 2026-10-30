from test_df_basic_statistics import test_run_process as test_df_basic_statistics_copy
from test_df_basic_statistics_add_to_df import (
    test_run_process as test_df_basic_statistics_add_to_df_copy,
)


def test_df_basic_statistics(data_exploration_run):
    test_df_basic_statistics_copy(data_exploration_run)


def test_df_basic_statistics_add_to_df(data_exploration_run):
    test_df_basic_statistics_add_to_df_copy(data_exploration_run)
