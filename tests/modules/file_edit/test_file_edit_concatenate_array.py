# TODO fix the code
import os

from test_utils import get_test_file_path
import sys

from assetutilities.engine import engine


def run_file(input_file, expected_result=None):
    if expected_result is None:
        expected_result = {}
    if input_file is not None and not os.path.isfile(input_file):
        input_file = get_test_file_path(input_file, os.path.dirname(__file__))
    engine(input_file)

    # obtained_result = cfg[cfg['basename']]['properties']
    # expected_result = expected_result[cfg['basename']]['properties'].copy()

    # assert not deepdiff.DeepDiff(obtained_result,
    #                              expected_result,
    #                              ignore_order=True,
    #                              significant_digits=4)


def get_valid_pytest_output_file(pytest_output_file):
    if pytest_output_file is not None and not os.path.isfile(pytest_output_file):
        pytest_output_file = get_test_file_path(pytest_output_file, os.path.dirname(__file__))
    return pytest_output_file


def test_file_run():
    input_file = "file_edit_concatenate_array.yml"

    # pytest_output_file = '../test_data/6d_buoy/buoy_6d_circular_px_0_pytest.yml'
    # pytest_output_file = get_valid_pytest_output_file(pytest_output_file)
    expected_result = {}
    # expected_result = ymlInput(pytest_output_file, updateYml=None)

    if len(sys.argv) > 1:
        sys.argv.pop()

    run_file(input_file, expected_result)


test_file_run()
