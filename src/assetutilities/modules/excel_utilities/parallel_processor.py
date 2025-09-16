"""
Parallel processing integration for Excel Utilities.
This module provides a bridge between assetutilities and the parallel processing
architecture inspired by digitalmodel.
"""
import os
import multiprocessing
from typing import Dict, Any, Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from loguru import logger


class ParallelProcessingConfig:
    """
    Configuration for parallel processing in Excel utilities.
    Adapted from digitalmodel's parallel processing architecture.
    """
    
    # Default settings optimized for Excel I/O operations
    DEFAULT_WORKERS_IO_BOUND = 8  # Optimal for file I/O operations
    DEFAULT_WORKERS_CPU_BOUND = multiprocessing.cpu_count()  # For CPU-intensive tasks
    DEFAULT_CHUNK_SIZE = 10  # Number of items per chunk for batch processing
    
    @staticmethod
    def get_optimal_workers(
        config_workers: Optional[Any] = 'auto',
        num_tasks: int = 0,
        task_type: str = 'io_bound',
        module_name: str = 'excel_utilities'
    ) -> Tuple[int, str]:
        """
        Determine optimal number of workers based on configuration and system resources.
        
        Args:
            config_workers: User configuration ('auto', number, or None)
            num_tasks: Number of tasks to process
            task_type: Type of task ('io_bound', 'cpu_bound', 'mixed')
            module_name: Name of the calling module for logging
            
        Returns:
            Tuple of (num_workers, log_message)
        """
        available_cores = multiprocessing.cpu_count()
        
        # Determine base number of workers
        if isinstance(config_workers, int):
            base_workers = config_workers
            source = "user-specified"
        elif config_workers == 'auto' or config_workers is None:
            if task_type == 'cpu_bound':
                base_workers = available_cores
                source = "CPU-bound default"
            else:  # io_bound or mixed
                base_workers = ParallelProcessingConfig.DEFAULT_WORKERS_IO_BOUND
                source = "I/O-bound default"
        else:
            base_workers = available_cores
            source = "fallback default"
        
        # Apply limits
        original_workers = base_workers
        
        # Don't exceed CPU count
        if base_workers > available_cores:
            workers = available_cores
            limit_reason = f"limited by {available_cores} CPU cores"
        else:
            workers = base_workers
            limit_reason = None
        
        # Don't exceed number of tasks
        if num_tasks > 0 and workers > num_tasks:
            workers = max(1, num_tasks)
            if limit_reason:
                limit_reason = f"{limit_reason}, then adjusted to {num_tasks} tasks"
            else:
                limit_reason = f"adjusted to {num_tasks} tasks"
        
        # Ensure at least 1 worker
        workers = max(1, workers)
        
        # Generate log message
        prefix = f"[{module_name}] " if module_name else ""
        
        if limit_reason:
            log_msg = f"{prefix}Using {workers} workers ({source}: {original_workers}, {limit_reason})"
        else:
            log_msg = f"{prefix}Using {workers} workers ({source})"
        
        return workers, log_msg


class ParallelExecutor:
    """
    Executor for parallel processing of Excel operations.
    Provides both thread-based and process-based execution.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the parallel executor.
        
        Args:
            config: Configuration dictionary with parallel processing settings
        """
        self.config = config or {}
        self.parallel_config = ParallelProcessingConfig()
    
    def should_use_parallel(self, num_items: int) -> Tuple[bool, int, str]:
        """
        Determine if parallel processing should be used.
        
        Args:
            num_items: Number of items to process
            
        Returns:
            Tuple of (use_parallel, num_workers, log_message)
        """
        parallel_settings = self.config.get('parallel_processing', {})
        
        # Check if parallel processing is enabled
        if not parallel_settings.get('enabled', True):
            return False, 1, "Parallel processing disabled in configuration"
        
        # Check if we have enough items to parallelize
        if num_items <= 1:
            return False, 1, "Single item - using sequential processing"
        
        # Get optimal number of workers
        workers, log_msg = self.parallel_config.get_optimal_workers(
            config_workers=parallel_settings.get('max_workers', 'auto'),
            num_tasks=num_items,
            task_type=parallel_settings.get('task_type', 'io_bound')
        )
        
        return True, workers, log_msg
    
    def execute_parallel_threads(
        self,
        func,
        items: List[Any],
        max_workers: int = None,
        callback=None
    ) -> List[Any]:
        """
        Execute function on items using thread pool.
        Best for I/O-bound operations like file reading/writing.
        
        Args:
            func: Function to execute on each item
            items: List of items to process
            max_workers: Maximum number of worker threads
            callback: Optional callback for progress updates
            
        Returns:
            List of results
        """
        if max_workers is None:
            use_parallel, max_workers, log_msg = self.should_use_parallel(len(items))
            logger.info(log_msg)
            
            if not use_parallel:
                # Fall back to sequential processing
                return [func(item) for item in items]
        
        results = []
        completed = 0
        total = len(items)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {executor.submit(func, item): item for item in items}
            
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    if callback:
                        callback(completed, total, result)
                    
                    logger.debug(f"Processed {completed}/{total} items")
                    
                except Exception as exc:
                    logger.error(f"Item {item} generated an exception: {exc}")
                    results.append(None)
        
        return results
    
    def execute_parallel_processes(
        self,
        func,
        items: List[Any],
        max_workers: int = None,
        callback=None
    ) -> List[Any]:
        """
        Execute function on items using process pool.
        Best for CPU-bound operations like data transformation.
        
        Args:
            func: Function to execute on each item
            items: List of items to process
            max_workers: Maximum number of worker processes
            callback: Optional callback for progress updates
            
        Returns:
            List of results
        """
        if max_workers is None:
            use_parallel, max_workers, log_msg = self.should_use_parallel(len(items))
            logger.info(log_msg)
            
            if not use_parallel:
                # Fall back to sequential processing
                return [func(item) for item in items]
        
        results = []
        completed = 0
        total = len(items)
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {executor.submit(func, item): item for item in items}
            
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    if callback:
                        callback(completed, total, result)
                    
                    logger.debug(f"Processed {completed}/{total} items")
                    
                except Exception as exc:
                    logger.error(f"Item {item} generated an exception: {exc}")
                    results.append(None)
        
        return results
    
    def batch_process(
        self,
        func,
        items: List[Any],
        batch_size: int = None,
        use_processes: bool = False
    ) -> List[Any]:
        """
        Process items in batches for better memory management.
        
        Args:
            func: Function to execute on each batch
            items: List of items to process
            batch_size: Size of each batch
            use_processes: Use process pool instead of thread pool
            
        Returns:
            List of results
        """
        if batch_size is None:
            batch_size = self.parallel_config.DEFAULT_CHUNK_SIZE
        
        # Create batches
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        
        # Process batches
        executor_func = self.execute_parallel_processes if use_processes else self.execute_parallel_threads
        
        logger.info(f"Processing {len(items)} items in {len(batches)} batches of size {batch_size}")
        
        batch_results = executor_func(func, batches)
        
        # Flatten results
        results = []
        for batch_result in batch_results:
            if batch_result:
                results.extend(batch_result)
        
        return results


# Convenience functions for common use cases
def process_excel_groups_parallel(groups: List[Dict], processor_func, config: Dict = None) -> List[Any]:
    """
    Process Excel groups in parallel using thread pool.
    
    Args:
        groups: List of group configurations
        processor_func: Function to process each group
        config: Optional configuration dictionary
        
    Returns:
        List of processing results
    """
    executor = ParallelExecutor(config)
    
    def progress_callback(completed, total, result):
        logger.info(f"Progress: {completed}/{total} groups processed")
    
    return executor.execute_parallel_threads(
        processor_func,
        groups,
        callback=progress_callback
    )


def process_csv_files_parallel(csv_files: List[str], processor_func, config: Dict = None) -> List[Any]:
    """
    Process CSV files in parallel using thread pool.
    
    Args:
        csv_files: List of CSV file paths
        processor_func: Function to process each CSV file
        config: Optional configuration dictionary
        
    Returns:
        List of processing results
    """
    executor = ParallelExecutor(config)
    return executor.execute_parallel_threads(processor_func, csv_files)


def transform_dataframes_parallel(dataframes: List, transformer_func, config: Dict = None) -> List[Any]:
    """
    Transform DataFrames in parallel using process pool (CPU-bound).
    
    Args:
        dataframes: List of pandas DataFrames
        transformer_func: Function to transform each DataFrame
        config: Optional configuration dictionary
        
    Returns:
        List of transformed DataFrames
    """
    executor = ParallelExecutor(config)
    
    # Override to use CPU-bound configuration
    if config is None:
        config = {}
    if 'parallel_processing' not in config:
        config['parallel_processing'] = {}
    config['parallel_processing']['task_type'] = 'cpu_bound'
    
    return executor.execute_parallel_processes(transformer_func, dataframes)