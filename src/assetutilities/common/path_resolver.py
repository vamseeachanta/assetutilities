"""
Path resolution utility for consistent handling of relative paths.
Ensures all relative paths are resolved from config directory when available.
"""

import os
from pathlib import Path
from typing import Optional, Union


class PathResolver:
    """Utility class for consistent path resolution across digitalmodel and assetutilities."""
    
    @staticmethod
    def resolve_path(path: Union[str, Path], cfg: dict = None, fallback_dir: str = None) -> str:
        """
        Resolve a path consistently, preferring config directory over current directory.
        
        Args:
            path: The path to resolve (can be relative or absolute)
            cfg: Configuration dictionary that may contain _config_dir_path
            fallback_dir: Directory to use if config dir not available (defaults to cwd)
            
        Returns:
            Absolute path as string
        """
        # Convert to string if Path object
        path = str(path)
        
        # If already absolute, return as-is
        if os.path.isabs(path):
            return path
            
        # Try to get config directory from cfg
        base_dir = None
        if cfg:
            # First try _config_dir_path (set by engine)
            base_dir = cfg.get("_config_dir_path")
            
            # Fallback to Analysis.analysis_root_folder if available
            if not base_dir:
                analysis_cfg = cfg.get("Analysis", {})
                if isinstance(analysis_cfg, dict):
                    base_dir = analysis_cfg.get("analysis_root_folder")
        
        # Use fallback directory if provided
        if not base_dir and fallback_dir:
            base_dir = fallback_dir
            
        # Final fallback to current working directory
        if not base_dir:
            base_dir = os.getcwd()
            
        # Resolve the path
        resolved = Path(base_dir) / path
        return str(resolved)
    
    @staticmethod
    def resolve_output_directory(cfg: dict, primary_key: str = "output_directory", 
                                secondary_key: str = "plot_directory",
                                fallback: str = "output") -> str:
        """
        Resolve output directory from config with fallback options.
        
        Args:
            cfg: Configuration dictionary
            primary_key: Primary key to check in visualization section
            secondary_key: Secondary key to check if primary not found
            fallback: Default path if no keys found
            
        Returns:
            Resolved absolute path
        """
        # Check visualization section first
        viz_cfg = cfg.get("visualization", {})
        output_dir = viz_cfg.get(primary_key)
        
        if not output_dir:
            output_dir = viz_cfg.get(secondary_key)
            
        # Check file_management section
        if not output_dir:
            fm_cfg = cfg.get("file_management", {})
            output_dir = fm_cfg.get(primary_key)
            
        # Check Analysis section for result folders
        if not output_dir:
            analysis_cfg = cfg.get("Analysis", {})
            if isinstance(analysis_cfg, dict):
                output_dir = analysis_cfg.get("result_plot_folder", 
                            analysis_cfg.get("result_folder", fallback))
        
        # Use fallback if still not found
        if not output_dir:
            output_dir = fallback
            
        # Resolve the path
        return PathResolver.resolve_path(output_dir, cfg)
    
    @staticmethod
    def ensure_config_tracking(cfg: dict, config_file_path: str = None) -> dict:
        """
        Ensure config dictionary has path tracking information.
        
        Args:
            cfg: Configuration dictionary to update
            config_file_path: Path to config file (optional)
            
        Returns:
            Updated configuration dictionary
        """
        if config_file_path and os.path.exists(config_file_path):
            cfg["_config_file_path"] = os.path.abspath(config_file_path)
            cfg["_config_dir_path"] = os.path.dirname(os.path.abspath(config_file_path))
        return cfg