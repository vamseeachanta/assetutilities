#!/usr/bin/env python3
"""
Test script for parallel Excel utilities processing.
Demonstrates the performance improvement from parallel processing.
"""
import os
import sys
import time
import yaml
from pathlib import Path
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import both versions for comparison
from assetutilities.modules.excel_utilities.excel_utilities import ExcelUtilities
from assetutilities.modules.excel_utilities.excel_utilities_parallel import ExcelUtilitiesParallel


def load_config(config_file: str) -> dict:
    """Load YAML configuration file."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def test_sequential_processing(config_file: str):
    """Test with sequential processing (original implementation)."""
    logger.info("=" * 50)
    logger.info("Testing SEQUENTIAL processing")
    logger.info("=" * 50)
    
    cfg = load_config(config_file)
    # Force sequential processing
    if 'parallel_processing' in cfg:
        cfg['parallel_processing']['enabled'] = False
    
    # Add Analysis section if missing
    if 'Analysis' not in cfg:
        cfg['Analysis'] = {
            'analysis_root_folder': str(Path(__file__).parent),
            'result_folder': str(Path(__file__).parent / 'output')
        }
    
    excel_util = ExcelUtilities()
    
    start_time = time.time()
    result = excel_util.excel_utility_router(cfg)
    elapsed_time = time.time() - start_time
    
    logger.info(f"Sequential processing completed in {elapsed_time:.2f} seconds")
    return elapsed_time


def test_parallel_processing(config_file: str):
    """Test with parallel processing (new implementation)."""
    logger.info("=" * 50)
    logger.info("Testing PARALLEL processing")
    logger.info("=" * 50)
    
    cfg = load_config(config_file)
    # Ensure parallel processing is enabled
    if 'parallel_processing' not in cfg:
        cfg['parallel_processing'] = {}
    cfg['parallel_processing']['enabled'] = True
    
    # Add Analysis section if missing
    if 'Analysis' not in cfg:
        cfg['Analysis'] = {
            'analysis_root_folder': str(Path(__file__).parent),
            'result_folder': str(Path(__file__).parent / 'output')
        }
    
    excel_util = ExcelUtilitiesParallel()
    
    start_time = time.time()
    result = excel_util.excel_utility_router(cfg)
    elapsed_time = time.time() - start_time
    
    logger.info(f"Parallel processing completed in {elapsed_time:.2f} seconds")
    
    # Log processing results if available
    if 'processing_results' in result:
        successful = sum(1 for r in result['processing_results'] if r['success'])
        total = len(result['processing_results'])
        logger.info(f"Processing results: {successful}/{total} successful")
    
    return elapsed_time


def create_test_data():
    """Create sample CSV files for testing if they don't exist."""
    test_dir = Path(__file__).parent / 'input_data'
    test_dir.mkdir(exist_ok=True)
    
    # Create sample inputs.csv
    inputs_file = test_dir / 'inputs.csv'
    if not inputs_file.exists():
        import pandas as pd
        df = pd.DataFrame({
            'ID': range(1, 101),
            'Value': [f'Value_{i}' for i in range(1, 101)],
            'Score': [i * 10 for i in range(1, 101)]
        })
        df.to_csv(inputs_file, index=False)
        logger.info(f"Created test file: {inputs_file}")
    
    # Create sample results.csv
    results_file = test_dir / 'results.csv'
    if not results_file.exists():
        import pandas as pd
        df = pd.DataFrame({
            'TestID': range(1, 51),
            'Result': ['Pass' if i % 2 == 0 else 'Fail' for i in range(1, 51)],
            'Metric': [i * 5.5 for i in range(1, 51)]
        })
        df.to_csv(results_file, index=False)
        logger.info(f"Created test file: {results_file}")


def main():
    """Main test function."""
    # Setup logging
    logger.add("parallel_processing_test.log", rotation="10 MB")
    
    # Create test data if needed
    create_test_data()
    
    # Test configuration files
    configs = [
        'copy_csv_to_excel.yml',  # Original config
        'copy_csv_to_excel_parallel.yml'  # New parallel config
    ]
    
    for config_file in configs:
        config_path = Path(__file__).parent / config_file
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            continue
        
        logger.info(f"\nTesting with config: {config_file}")
        
        # Test sequential processing
        try:
            seq_time = test_sequential_processing(str(config_path))
        except Exception as e:
            logger.error(f"Sequential processing failed: {e}")
            seq_time = None
        
        # Test parallel processing
        try:
            par_time = test_parallel_processing(str(config_path))
        except Exception as e:
            logger.error(f"Parallel processing failed: {e}")
            par_time = None
        
        # Compare results
        if seq_time and par_time:
            speedup = seq_time / par_time if par_time > 0 else 1
            improvement = (seq_time - par_time) / seq_time * 100 if seq_time > 0 else 0
            
            logger.info("\n" + "=" * 50)
            logger.info("PERFORMANCE COMPARISON")
            logger.info("=" * 50)
            logger.info(f"Sequential Time: {seq_time:.2f} seconds")
            logger.info(f"Parallel Time:   {par_time:.2f} seconds")
            logger.info(f"Speedup:         {speedup:.2f}x")
            logger.info(f"Improvement:     {improvement:.1f}%")
            logger.info("=" * 50)


if __name__ == "__main__":
    main()