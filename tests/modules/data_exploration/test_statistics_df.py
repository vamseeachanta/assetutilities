def test_run_process(data_exploration_run):
    input_file = "df_statistics_file_management.yml"
    result = data_exploration_run(input_file)
    assert result is not None
