# Standard library imports
import os
import sys

# Reader imports
from assetutilities.engine import engine


def run_process(input_file, expected_result={}):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    cfg = engine(input_file)

def get_valid_pytest_output_file(pytest_output_file):
    if pytest_output_file is not None and not os.path.isfile(
            pytest_output_file):
        pytest_output_file = os.path.join(os.path.dirname(__file__),
                                          pytest_output_file)
    return pytest_output_file


def test_run_process():
    input_file = 'csv_with_latin1.yml'
    input_file = get_valid_pytest_output_file(input_file)

    pytest_output_file = None

    if len(sys.argv) > 1:
        sys.argv.pop()

    run_process(input_file, expected_result={})


test_run_process()