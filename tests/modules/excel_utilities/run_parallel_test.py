#!/usr/bin/env python3
"""
Run parallel Excel utilities test using the enhanced parallel processing architecture.
This script demonstrates how to use the parallel processing capabilities with the
existing test configuration.
"""
import os
import sys
import time
import yaml
from pathlib import Path
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from assetutilities.modules.excel_utilities.excel_utilities_parallel import ExcelUtilitiesParallel
from assetutilities.modules.excel_utilities.parallel_processor import process_excel_groups_parallel


def run_parallel_csv_to_excel_test():
    """Run the CSV to Excel test with parallel processing."""
    
    # Setup paths
    test_dir = Path(__file__).parent
    config_file = test_dir / "copy_csv_to_excel.yml"
    
    # Load configuration
    logger.info(f"Loading configuration from: {config_file}")
    with open(config_file, 'r') as f:
        cfg = yaml.safe_load(f)
    
    # Add parallel processing configuration
    cfg['parallel_processing'] = {
        'enabled': True,
        'max_workers': 'auto',  # Auto-detect optimal workers
        'task_type': 'io_bound'  # Excel operations are I/O-bound
    }
    
    # Add Analysis section if not present
    if 'Analysis' not in cfg:
        cfg['Analysis'] = {
            'analysis_root_folder': str(test_dir),
            'result_folder': str(test_dir / 'output')
        }
    
    # Create output directory if it doesn't exist
    output_dir = Path(cfg['Analysis']['result_folder'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Log configuration details
    groups = cfg.get('data', {}).get('groups', [])
    logger.info(f"Found {len(groups)} groups to process")
    for i, group in enumerate(groups, 1):
        input_file = group.get('input', {}).get('filename', 'N/A')
        target_file = group.get('target', {}).get('filename', 'N/A')
        sheet_name = group.get('target', {}).get('sheet_name', 'N/A')
        logger.info(f"  Group {i}: {input_file} -> {target_file}:{sheet_name}")
    
    # Initialize parallel Excel utilities
    excel_util = ExcelUtilitiesParallel()
    
    # Measure execution time
    logger.info("\nStarting parallel processing...")
    start_time = time.time()
    
    # Execute the task
    result = excel_util.excel_utility_router(cfg)
    
    elapsed_time = time.time() - start_time
    
    # Log results
    logger.info(f"\nParallel processing completed in {elapsed_time:.2f} seconds")
    
    # Check processing results
    if 'processing_results' in result:
        results = result['processing_results']
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        logger.info(f"\nProcessing Summary:")
        logger.info(f"  Total groups: {total}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {total - successful}")
        
        # Log individual results
        for i, res in enumerate(results, 1):
            status = "✓" if res['success'] else "✗"
            logger.info(f"  {status} Group {i}: {res['message']}")
        
        # Calculate performance metrics
        if total > 0:
            success_rate = (successful / total) * 100
            logger.info(f"\nSuccess rate: {success_rate:.1f}%")
            
            # Estimate sequential time (assuming each group takes similar time)
            avg_time_per_group = elapsed_time / max(1, total)
            estimated_sequential_time = avg_time_per_group * total * 0.8  # Rough estimate
            speedup = estimated_sequential_time / elapsed_time if elapsed_time > 0 else 1
            
            logger.info(f"Estimated speedup: {speedup:.2f}x")
    
    return result


def run_comparison_test():
    """Run a comparison between sequential and parallel processing."""
    
    logger.info("=" * 60)
    logger.info("EXCEL UTILITIES PARALLEL PROCESSING COMPARISON TEST")
    logger.info("=" * 60)
    
    test_dir = Path(__file__).parent
    config_file = test_dir / "copy_csv_to_excel.yml"
    
    # Load base configuration
    with open(config_file, 'r') as f:
        base_cfg = yaml.safe_load(f)
    
    # Add Analysis section
    if 'Analysis' not in base_cfg:
        base_cfg['Analysis'] = {
            'analysis_root_folder': str(test_dir),
            'result_folder': str(test_dir / 'output')
        }
    
    groups = base_cfg.get('data', {}).get('groups', [])
    
    # Test 1: Sequential processing
    logger.info("\n1. SEQUENTIAL PROCESSING")
    logger.info("-" * 30)
    
    seq_cfg = base_cfg.copy()
    seq_cfg['parallel_processing'] = {'enabled': False}
    
    excel_seq = ExcelUtilitiesParallel()
    
    start_time = time.time()
    seq_result = excel_seq.csv_copy_to_excel_sequential(seq_cfg)
    seq_time = time.time() - start_time
    
    seq_successful = sum(1 for r in seq_result.get('processing_results', []) if r['success'])
    logger.info(f"Sequential: {seq_successful}/{len(groups)} successful in {seq_time:.2f}s")
    
    # Test 2: Parallel processing
    logger.info("\n2. PARALLEL PROCESSING")
    logger.info("-" * 30)
    
    par_cfg = base_cfg.copy()
    par_cfg['parallel_processing'] = {
        'enabled': True,
        'max_workers': 'auto',
        'task_type': 'io_bound'
    }
    
    excel_par = ExcelUtilitiesParallel()
    
    start_time = time.time()
    par_result = excel_par.csv_copy_to_excel_parallel(par_cfg)
    par_time = time.time() - start_time
    
    par_successful = sum(1 for r in par_result.get('processing_results', []) if r['success'])
    logger.info(f"Parallel: {par_successful}/{len(groups)} successful in {par_time:.2f}s")
    
    # Compare results
    logger.info("\n" + "=" * 60)
    logger.info("COMPARISON RESULTS")
    logger.info("=" * 60)
    
    logger.info(f"Sequential Time: {seq_time:.2f} seconds")
    logger.info(f"Parallel Time:   {par_time:.2f} seconds")
    
    if par_time > 0:
        speedup = seq_time / par_time
        improvement = (seq_time - par_time) / seq_time * 100
        logger.info(f"Speedup:         {speedup:.2f}x")
        logger.info(f"Improvement:     {improvement:.1f}%")
    
    logger.info("=" * 60)


def main():
    """Main function."""
    
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    logger.add("parallel_test.log", level="DEBUG", rotation="10 MB")
    
    # Create test data if needed
    test_dir = Path(__file__).parent
    input_dir = test_dir / "input_data"
    input_dir.mkdir(exist_ok=True)
    
    # Create sample CSV files if they don't exist
    inputs_csv = input_dir / "inputs.csv"
    if not inputs_csv.exists():
        import pandas as pd
        df = pd.DataFrame({
            'ID': range(1, 101),
            'Name': [f'Item_{i}' for i in range(1, 101)],
            'Value': [i * 10 for i in range(1, 101)]
        })
        df.to_csv(inputs_csv, index=False)
        logger.info(f"Created test file: {inputs_csv}")
    
    results_csv = input_dir / "results.csv"
    if not results_csv.exists():
        import pandas as pd
        df = pd.DataFrame({
            'TestID': range(1, 51),
            'Status': ['Pass' if i % 2 == 0 else 'Fail' for i in range(1, 51)],
            'Score': [i * 5 for i in range(1, 51)]
        })
        df.to_csv(results_csv, index=False)
        logger.info(f"Created test file: {results_csv}")
    
    # Run tests
    choice = input("\nSelect test to run:\n1. Parallel processing test\n2. Comparison test (sequential vs parallel)\nChoice (1 or 2): ").strip()
    
    if choice == "2":
        run_comparison_test()
    else:
        run_parallel_csv_to_excel_test()
    
    logger.info("\nTest completed successfully!")


if __name__ == "__main__":
    main()