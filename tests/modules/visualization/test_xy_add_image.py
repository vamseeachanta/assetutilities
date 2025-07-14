# Standard library imports
import os

# Reader imports
from assetutilities.engine import engine


def run_visualization_polar(input_file):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    engine(input_file)


def get_valid_pytest_output_file(pytest_output_file):
    if pytest_output_file is not None and not os.path.isfile(pytest_output_file):
        pytest_output_file = os.path.join(os.path.dirname(__file__), pytest_output_file)
    return pytest_output_file


def test_visualization_polar():
    input_file = "visualization_xy_add_image.yml"
    # pytest_output_file = '../test_data/6d_buoy/buoy_6d_circular_px_0_pytest.yml'
    # pytest_output_file = get_valid_pytest_output_file(pytest_output_file)
    # expected_result removed; not used
    # expected_result = ymlInput(pytest_output_file, updateYml=None)

    # Do not manipulate sys.argv in pytest tests
    run_visualization_polar(input_file)
