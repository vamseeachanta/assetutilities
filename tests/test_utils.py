"""
Common test utilities for AssetUtilities tests.

This module provides helper functions for consistent path resolution
across all test files, preventing the common YAML parsing errors.
"""

import os
import sys
from pathlib import Path


def get_test_file_path(test_file_name, test_file_directory=None):
    """
    Get the correct path to a test file (YAML, CSV, etc.) regardless of where the test is run from.
    
    Args:
        test_file_name (str): Name of the test file (e.g., 'test_config.yml')
        test_file_directory (str): Directory where the test file is located. 
                                   If None, uses the calling test's directory.
    
    Returns:
        str: Absolute path to the test file
        
    Example:
        # In test_zip_by_stem.py
        from test_utils import get_test_file_path
        
        def test_run_process():
            input_file = get_test_file_path('test_zip_by_stem.yml')
            result = run_process(input_file)
    """
    # Get the directory of the calling test file
    if test_file_directory is None:
        # Get the frame of the caller
        import inspect
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        caller_file = caller_frame.f_globals.get('__file__', '')
        test_file_directory = os.path.dirname(os.path.abspath(caller_file))
    
    # Build the full path
    full_path = os.path.join(test_file_directory, test_file_name)
    
    # If the file doesn't exist at the full path, check if it's a relative path
    if not os.path.exists(full_path):
        # Try to find it relative to the test directory
        if os.path.exists(test_file_name):
            full_path = os.path.abspath(test_file_name)
    
    return full_path


def run_process_with_correct_path(input_file, engine_func):
    """
    Run the engine process with correct file path resolution.
    
    Args:
        input_file (str): Name or path to the input file
        engine_func: The engine function to call (usually from assetutilities.engine import engine)
    
    Returns:
        dict: Configuration dictionary from the engine
        
    Example:
        from assetutilities.engine import engine
        from test_utils import run_process_with_correct_path
        
        def test_run_process():
            result = run_process_with_correct_path('test_config.yml', engine)
            assert result is not None
    """
    # Get the correct file path
    if input_file is not None:
        # Get caller's directory for relative path resolution
        import inspect
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        caller_file = caller_frame.f_globals.get('__file__', '')
        caller_dir = os.path.dirname(os.path.abspath(caller_file))
        
        # Check if file exists relative to caller's directory
        test_path = os.path.join(caller_dir, input_file)
        if os.path.exists(test_path):
            input_file = test_path
        elif not os.path.isabs(input_file) and not os.path.exists(input_file):
            # If it's not absolute and doesn't exist, make it relative to caller
            input_file = test_path
    
    # Call the engine with the corrected path
    cfg = engine_func(input_file)
    return cfg


def setup_test_environment():
    """
    Setup the test environment to ensure proper imports and paths.
    
    This should be called at the beginning of test files if needed.
    """
    # Ensure the project root is in the Python path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Ensure src is in the path for imports
    src_path = project_root / 'src'
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    return project_root


def get_test_data_dir(module_name):
    """
    Get the test data directory for a specific module.
    
    Args:
        module_name (str): Name of the module (e.g., 'zip_utilities', 'excel_utilities')
    
    Returns:
        Path: Path object to the test data directory
    """
    tests_root = Path(__file__).parent
    module_test_dir = tests_root / 'modules' / module_name
    return module_test_dir


def create_temp_test_file(content, suffix='.yml', prefix='test_', directory=None):
    """
    Create a temporary test file with given content.
    
    Args:
        content (str): Content to write to the file
        suffix (str): File extension (default: '.yml')
        prefix (str): File prefix (default: 'test_')
        directory (str): Directory to create the file in (default: temp directory)
    
    Returns:
        str: Path to the created temporary file
    """
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, prefix=prefix, 
                                      dir=directory, delete=False) as f:
        f.write(content)
        return f.name


class TestFileResolver:
    """
    Context manager for resolving test file paths within a test.
    
    Example:
        with TestFileResolver() as resolver:
            config_file = resolver.get_file('test_config.yml')
            result = engine(config_file)
    """
    
    def __init__(self):
        import inspect
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        self.caller_file = caller_frame.f_globals.get('__file__', '')
        self.test_dir = os.path.dirname(os.path.abspath(self.caller_file))
        self.original_cwd = os.getcwd()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original working directory if changed
        if os.getcwd() != self.original_cwd:
            os.chdir(self.original_cwd)
    
    def get_file(self, filename):
        """Get the full path to a test file."""
        full_path = os.path.join(self.test_dir, filename)
        if os.path.exists(full_path):
            return full_path
        # Try relative to current directory as fallback
        if os.path.exists(filename):
            return os.path.abspath(filename)
        # Return the full path even if it doesn't exist (let the test handle the error)
        return full_path
    
    def change_to_test_dir(self):
        """Change to the test directory for the duration of the test."""
        os.chdir(self.test_dir)
        return self.test_dir


# Backwards compatibility function for existing tests
def run_process(input_file):
    """
    Legacy function for backward compatibility with existing tests.
    
    This function is provided to maintain compatibility with existing test files
    that use the run_process pattern. New tests should use the functions above.
    
    Args:
        input_file (str): Input file name or path
    
    Returns:
        dict: Configuration from engine
    """
    from assetutilities.engine import engine
    
    # Get the caller's directory
    import inspect
    frame = inspect.currentframe()
    caller_frame = frame.f_back
    caller_file = caller_frame.f_globals.get('__file__', '')
    caller_dir = os.path.dirname(os.path.abspath(caller_file))
    
    # Resolve the file path
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(caller_dir, input_file)
    
    cfg = engine(input_file)
    return cfg