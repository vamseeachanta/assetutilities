# Standard library imports
import os
import sys
import deepdiff

import colorama
from assetutilities.common.yml_utilities import ymlInput

# Reader imports
from assetutilities.engine import engine
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

    # obtained_result = cfg[cfg['basename']]['divide']
    # expected_result = expected_result[cfg['basename']]['divide'].copy()

    # for group_index, group_ele in enumerate(obtained_result['groups']):
    #     for data_index, data_ele in enumerate(group_ele[group_index]):
    #         file_obtained = obtained_result['groups'][group_index][data_index]['data']
    #         file_expected = expected_result['groups'][group_index][data_index]['data']

    #         file_obtained_yml = ymlInput(file_obtained)
    #         file_expected_yml = ymlInput(file_expected)
            
    #         assert not deepdiff.DeepDiff(
    #             file_obtained_yml, file_expected_yml, ignore_order=True, significant_digits=4
    #         )

    return cfg


def test_run_process():
    input_file = "ruamel_test_primary_key.yml"

    # pytest_output_file = "results/divide_yaml_file_by_primary_key_pytest.yml"
    # pytest_output_file = tu.get_valid_pytest_output_file(os.path.dirname(__file__), pytest_output_file)
    # expected_result = ymlInput(pytest_output_file, updateYml=None)


    if len(sys.argv) > 1:
        sys.argv.pop()

    run_process(input_file, expected_result={})


test_run_process()
