import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from assetutilities.engine import engine
from test_utils import get_test_file_path


def run_process(input_file):
    # Use the common test utility for proper path resolution
    input_file = get_test_file_path(input_file, os.path.dirname(__file__))
    result = engine(input_file)
    return result


def test_run_process():
    input_file = 'copy_csv_to_excel.yml'
    result = run_process(input_file)
    assert result is not None