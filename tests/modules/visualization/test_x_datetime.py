import os
from src.assetutilities.engine import engine


def run_visualization(input_file):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    result = engine(input_file)
    return result


def test_visualization():
    input_file = "template_x_datetime_matplotlib.yml"
    result = run_visualization(input_file)
    assert result is not None


test_visualization()
