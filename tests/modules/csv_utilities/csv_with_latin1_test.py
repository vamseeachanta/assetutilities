import os

import pytest

from assetutilities.engine import engine


def run_process(input_file):
    # Fixed path resolution to prevent YAML parsing errors
    if input_file is not None:
        # Always resolve path relative to this test file's directory
        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_file_path = os.path.join(test_dir, input_file)
        
        # Check if file exists at the resolved path
        if os.path.exists(test_file_path):
            input_file = test_file_path
        elif not os.path.isabs(input_file) and not os.path.exists(input_file):
            # If relative and doesn't exist, use test directory path
            input_file = test_file_path
    
    cfg = engine(input_file)
    return cfg


@pytest.mark.xfail(
    reason=(
        "csv_utilities router is an unimplemented loud stub — see engine.py. "
        "CSVUtilitiesRouter.router is a no-op (its only branch is `pass`) and "
        "CSVUtilities is an internal zip_utilities helper that reads a zip "
        "file-object, not a standalone path workflow. The engine now raises "
        "NotImplementedError for basename 'csv_utilities' (PR #95). This test "
        "previously passed only because the old silent no-op returned an "
        "unchanged cfg; it never exercised real csv_utilities behavior."
    ),
    raises=NotImplementedError,
    strict=False,
)
def test_run_process():
    input_file = "csv_with_latin1.yml"
    result = run_process(input_file)
    assert result is not None
