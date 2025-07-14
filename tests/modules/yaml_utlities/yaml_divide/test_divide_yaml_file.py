import os

from src.assetutilities.engine import engine


def run_process(input_file):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    result = engine(input_file)
    return result


def test_run_process():
    input_file = "divide_yaml_file.yml"
    result = run_process(input_file)
    assert result is not None
    input_file = "divide_yaml_file_by_primary_key.yml"

    # pytest_output_file = "results/divide_yaml_file_by_primary_key_pytest.yml"
    # pytest_output_file = tu.get_valid_pytest_output_file(os.path.dirname(__file__), pytest_output_file)
    # expected_result = ymlInput(pytest_output_file, updateYml=None)

    if len(sys.argv) > 1:
        sys.argv.pop()

    run_process(input_file, expected_result={})


test_run_process()
