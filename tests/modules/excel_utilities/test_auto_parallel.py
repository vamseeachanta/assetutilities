#!/usr/bin/env python3
"""
Automated test for parallel Excel utilities processing.
Runs without requiring user input.
"""
import os
import sys
import time
import yaml
from pathlib import Path
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from assetutilities.modules.excel_utilities.excel_utilities import ExcelUtilities
from assetutilities.modules.excel_utilities.excel_utilities_parallel import ExcelUtilitiesParallel


def setup_test_data():
    """Create test data if it doesn't exist."""
    test_dir = Path(__file__).parent
    input_dir = test_dir / "input_data"
    input_dir.mkdir(exist_ok=True)
    
    # Create sample inputs.csv
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
    
    # Create sample results.csv  
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
    
    return test_dir


def test_parallel_processing():
    """Test parallel processing of Excel utilities."""
    test_dir = setup_test_data()
    config_file = test_dir / "copy_csv_to_excel.yml"
    
    # Load configuration
    logger.info(f"Loading configuration from: {config_file}")
    with open(config_file, 'r') as f:
        cfg = yaml.safe_load(f)
    
    # Add parallel processing configuration
    cfg['parallel_processing'] = {
        'enabled': True,
        'max_workers': 'auto',
        'task_type': 'io_bound'
    }
    
    # Add Analysis section if not present - use absolute path
    if 'Analysis' not in cfg:
        cfg['Analysis'] = {
            'analysis_root_folder': str(test_dir.resolve()),
            'result_folder': str((test_dir / 'output').resolve())
        }
    else:
        # Ensure analysis_root_folder is set correctly
        cfg['Analysis']['analysis_root_folder'] = str(test_dir.resolve())
    
    # Create output directory
    output_dir = Path(cfg['Analysis']['result_folder'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    groups = cfg.get('data', {}).get('groups', [])
    logger.info(f"Found {len(groups)} groups to process")
    
    # Test with parallel processing
    logger.info("\n" + "=" * 60)
    logger.info("TESTING PARALLEL PROCESSING")
    logger.info("=" * 60)
    
    excel_util = ExcelUtilitiesParallel()
    
    start_time = time.time()
    result = excel_util.excel_utility_router(cfg)
    elapsed_time = time.time() - start_time
    
    logger.info(f"Parallel processing completed in {elapsed_time:.2f} seconds")
    
    # Check results
    if 'processing_results' in result:
        results = result['processing_results']
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        logger.info(f"\nProcessing Summary:")
        logger.info(f"  Total groups: {total}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {total - successful}")
        
        for i, res in enumerate(results, 1):
            status = "✓" if res['success'] else "✗"
            logger.info(f"  {status} Group {i}: {res['message']}")
        
        # Check if test passed
        if successful == total:
            logger.success(f"\n✅ TEST PASSED: All {total} groups processed successfully!")
            return True
        else:
            logger.error(f"\n❌ TEST FAILED: Only {successful}/{total} groups succeeded")
            return False
    else:
        logger.error("\n❌ TEST FAILED: No processing results found")
        return False


def run_comparison_test():
    """Compare sequential vs parallel processing."""
    test_dir = setup_test_data()
    config_file = test_dir / "copy_csv_to_excel.yml"
    
    # Load base configuration
    with open(config_file, 'r') as f:
        base_cfg = yaml.safe_load(f)
    
    # Add Analysis section - use absolute path
    if 'Analysis' not in base_cfg:
        base_cfg['Analysis'] = {
            'analysis_root_folder': str(test_dir.resolve()),
            'result_folder': str((test_dir / 'output').resolve())
        }
    else:
        # Ensure analysis_root_folder is set correctly
        base_cfg['Analysis']['analysis_root_folder'] = str(test_dir.resolve())
    
    groups = base_cfg.get('data', {}).get('groups', [])
    
    logger.info("\n" + "=" * 60)
    logger.info("COMPARISON: SEQUENTIAL VS PARALLEL")
    logger.info("=" * 60)
    
    # Test 1: Sequential processing
    logger.info("\n1. SEQUENTIAL PROCESSING")
    seq_cfg = base_cfg.copy()
    seq_cfg['parallel_processing'] = {'enabled': False}
    
    excel_seq = ExcelUtilitiesParallel()
    start_time = time.time()
    seq_result = excel_seq.csv_copy_to_excel_sequential(seq_cfg)
    seq_time = time.time() - start_time
    
    seq_successful = sum(1 for r in seq_result.get('processing_results', []) if r['success'])
    logger.info(f"Sequential: {seq_successful}/{len(groups)} successful in {seq_time:.3f}s")
    
    # Test 2: Parallel processing
    logger.info("\n2. PARALLEL PROCESSING")
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
    logger.info(f"Parallel: {par_successful}/{len(groups)} successful in {par_time:.3f}s")
    
    # Compare results
    logger.info("\n" + "=" * 60)
    logger.info("PERFORMANCE COMPARISON")
    logger.info("=" * 60)
    
    logger.info(f"Sequential Time: {seq_time:.3f} seconds")
    logger.info(f"Parallel Time:   {par_time:.3f} seconds")
    
    if par_time > 0 and seq_time > par_time:
        speedup = seq_time / par_time
        improvement = (seq_time - par_time) / seq_time * 100
        logger.info(f"Speedup:         {speedup:.2f}x")
        logger.info(f"Improvement:     {improvement:.1f}%")
        logger.success("\n✅ Parallel processing is faster!")
    elif seq_time <= par_time:
        logger.warning("\n⚠️ Sequential is faster (likely due to small dataset or overhead)")
    
    logger.info("=" * 60)
    
    return par_successful == seq_successful == len(groups)


def main():
    """Main test function."""
    # Configure logging
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    logger.add("test_parallel_auto.log", level="DEBUG", rotation="10 MB")
    
    logger.info("Starting automated parallel processing test...")
    
    # Run basic parallel test
    test_passed = test_parallel_processing()
    
    # Run comparison test
    logger.info("\n" + "=" * 60)
    logger.info("Running comparison test...")
    comparison_passed = run_comparison_test()
    
    # Final result
    logger.info("\n" + "=" * 60)
    logger.info("FINAL TEST RESULTS")
    logger.info("=" * 60)
    
    if test_passed and comparison_passed:
        logger.success("✅ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        logger.error("❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()