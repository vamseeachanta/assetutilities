"""
Not worked as intended. Difficult to work between Excel workbooks to keep live links.
Easier to just do a brute force copy and paste and rerun script if needed.
"""

# Standard library imports
import os
import sys

# Third party imports
import pytest


# Reader imports
from assetutilities.engine import engine


@pytest.mark.skip(reason="Only works in local drive")
def run_excel_utilties_closed_file_reference(input_file, expected_result={}):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    cfg = engine(input_file)

    # obtained_result = cfg[cfg['basename']]['properties']
    # expected_result = expected_result[cfg['basename']]['properties'].copy()

    # assert not deepdiff.DeepDiff(obtained_result,
    #                              expected_result,
    #                              ignore_order=True,
    #                              significant_digits=4)


@pytest.mark.skip(reason="Only works in local drive")
def get_valid_pytest_output_file(pytest_output_file):
    if pytest_output_file is not None and not os.path.isfile(pytest_output_file):
        pytest_output_file = os.path.join(os.path.dirname(__file__), pytest_output_file)
    return pytest_output_file

@pytest.mark.skip(reason="Only works in local drive")
def test_excel_utilties_closed_file_reference():
    input_file = "test_data/excel_utilities/excel_utilities_excel_to_image.yml"

    # pytest_output_file = '../test_data/6d_buoy/buoy_6d_circular_px_0_pytest.yml'
    # pytest_output_file = get_valid_pytest_output_file(pytest_output_file)
    expected_result = {}
    # expected_result = ymlInput(pytest_output_file, updateYml=None)

    if len(sys.argv) > 1:
        sys.argv.pop()

    run_excel_utilties_closed_file_reference(input_file, expected_result)


test_excel_utilties_closed_file_reference()
