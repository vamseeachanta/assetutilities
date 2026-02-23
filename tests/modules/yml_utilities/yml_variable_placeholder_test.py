# Standard library imports
import os
import sys

import colorama

from assetutilities.common.yml_utilities import ymlInput  # noqa

# Reader imports
from assetutilities.engine import engine  # noqa
from assetutilities.modules.test_utilities.test_utilities import TestUtilities

colorama.init(autoreset=True)

tu = TestUtilities()


def run_process(input_file, expected_result):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    cfg = engine(input_file)

    input = cfg["define"]
    output = cfg["data"]["groups"][0]["label"]

    assert input == output, f"Expected {input} to be equal to {output}"

    return cfg


def test_run_process():
    input_file = "yml_variable_placeholder.yml"

    # pytest_output_file = "results/divide_yaml_file_by_primary_key_pytest.yml"
    # pytest_output_file = tu.get_valid_pytest_output_file(os.path.dirname(__file__), pytest_output_file)
    # expected_result = ymlInput(pytest_output_file, updateYml=None)

    if len(sys.argv) > 1:
        sys.argv.pop()

    run_process(input_file, expected_result={})


test_run_process()
