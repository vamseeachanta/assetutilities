def test_run_process(data_exploration_run):
    input_file = "df_basic_statistics_add_to_df.yml"
    result = data_exploration_run(input_file)
    assert result is not None
