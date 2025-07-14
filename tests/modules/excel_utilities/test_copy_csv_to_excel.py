import os
from src.assetutilities.engine import engine


def run_process(input_file):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    result = engine(input_file)
    return result


def test_run_process():
    input_file = 'copy_csv_to_excel.yml'
    result = run_process(input_file)
    assert result is not None
        sys.argv.pop()

    run_process(input_file, expected_result={})


test_run_process()