import os
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


def test_run_process():
    input_file = "web_scraping_scrapy.yml"
    result = run_process(input_file)
    assert result is not None
