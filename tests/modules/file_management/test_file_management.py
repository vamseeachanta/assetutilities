# Standard library imports
import os
import sys

# Third party imports
import colorama

# Reader imports
from assetutilities.common.yml_utilities import ymlInput
from assetutilities.engine import engine
from assetutilities.modules.test_utilities.test_utilities import TestUtilities

colorama.init(autoreset=True)

# Standard library imports

tu = TestUtilities()

def run_process(input_file, expected_result):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    cfg = engine(input_file)

    return cfg


def test_run_process():
    input_file = "test_file_management_contains_not_contains.yml"

    # pytest_output_file = "results/test_zip_by_stem_pytest.yml"
    # pytest_output_file = tu.get_valid_pytest_output_file(os.path.dirname(__file__), pytest_output_file)
    # expected_result = ymlInput(pytest_output_file, updateYml=None)


    if len(sys.argv) > 1:
        sys.argv.pop()

    run_process(input_file, expected_result={})


test_run_process()
