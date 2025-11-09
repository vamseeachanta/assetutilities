"""
Excel Utilities module for AssetUtilities.
Provides both sequential and parallel processing capabilities.
"""

from .excel_utilities import ExcelUtilities
from .excel_utilities_parallel import ExcelUtilitiesParallel
from .parallel_processor import (
    ParallelExecutor,
    ParallelProcessingConfig,
    process_excel_groups_parallel,
    process_csv_files_parallel,
    transform_dataframes_parallel
)

__all__ = [
    'ExcelUtilities',
    'ExcelUtilitiesParallel',
    'ParallelExecutor',
    'ParallelProcessingConfig',
    'process_excel_groups_parallel',
    'process_csv_files_parallel',
    'transform_dataframes_parallel'
]

# Set default implementation
# Users can import ExcelUtilities and get parallel processing by default
# with backward compatibility for existing code
ExcelUtilitiesDefault = ExcelUtilitiesParallel