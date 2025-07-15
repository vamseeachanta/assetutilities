import os
from assetutilities.engine import engine


def run_visualization_polar(input_file):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    result = engine(input_file)
    return result


def test_visualization_polar():
    input_file = "test_data/visualization/visualization_polar_plotly.yml"
    result = run_visualization_polar(input_file)
    assert result is not None


# test_visualization_polar()
