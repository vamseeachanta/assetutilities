import os

from assetutilities.engine import engine


def run_visualization_polar(input_file):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    result = engine(input_file)
    return result


def test_visualization_polar():
    input_file = "visualization_polar_midsplice_deck_handling.yml"
    result = run_visualization_polar(input_file)
    assert result is not None
