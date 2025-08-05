import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from test_utils import get_test_file_path

import pytest

from assetutilities.engine import engine


@pytest.mark.skip(reason="Only works in local drive")
def test_word_utilties_search_string():
    input_file = "word_csv_to_docx.yml"
    if input_file is not None and not os.path.isfile(input_file):
        input_file = get_test_file_path(input_file, os.path.dirname(__file__))
    result = engine(input_file)
    assert result is not None
    # input_file = 'src/assetutlities/tests/test_data/word_utilities/word_utilities.yml'
    input_file = "word_utilities_df_to_docx.yml"

    # pytest_output_file = '../test_data/6d_buoy/buoy_6d_circular_px_0_pytest.yml'
    # pytest_output_file = get_valid_pytest_output_file(pytest_output_file)
    expected_result = {}
    # expected_result = ymlInput(pytest_output_file, updateYml=None)

    if len(sys.argv) > 1:
        sys.argv.pop()

    run_word_utilties_search_string(input_file, expected_result)


test_word_utilties_search_string()
