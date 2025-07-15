test_run_process()
import os

from assetutilities.engine import engine


def run_process(input_file):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    result = engine(input_file)
    return result


def test_run_process():
    input_file = "test_plot_from_yml_example_data1.yml"
    result = run_process(input_file)
    assert result is not None
