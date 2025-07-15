import os

from assetutilities.engine import engine


def run_process(input_file):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    cfg = engine(input_file)
    return cfg


def test_run_process():
    input_file = "csv_with_latin1.yml"
    result = run_process(input_file)
    assert result is not None
