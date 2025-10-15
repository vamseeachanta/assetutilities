# ABOUTME: Pytest configuration file that adds tests directory to Python path
# ABOUTME: This enables all test files to import test_utils module

import sys
import pytest
from pathlib import Path

# Add tests directory to Python path so test_utils can be imported from subdirectories
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))


@pytest.fixture
def config_file():
    """
    Fixture providing a test configuration file path.
    Returns the path to a test YAML configuration file.
    """
    # Return a generic test config file path that can be overridden by tests
    return str(tests_dir / "test_config.yml")
