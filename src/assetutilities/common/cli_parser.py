"""
CLI argument parser for modern command-line interfaces.

This module provides utilities to parse modern CLI arguments in various formats,
supporting both legacy dictionary format and modern --key value format.
"""

import sys
from typing import Dict, List, Any, Tuple, Optional


def parse_cli_arguments(args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Parse command-line arguments in modern format.
    
    Supports:
    - --key value
    - --key subkey=value
    - --key subkey1=value1 subkey2=value2
    - Mixed formats
    
    Args:
        args: List of arguments to parse. If None, uses sys.argv[2:]
        
    Returns:
        Dictionary of parsed arguments
    
    Examples:
        >>> parse_cli_arguments(['--meta', 'label=test', '--workers', '10'])
        {'meta': {'label': 'test'}, 'workers': '10'}
        
        >>> parse_cli_arguments(['--file_management', 'input_dir=./input', 
        ...                      'output_dir=./output'])
        {'file_management': {'input_dir': './input', 'output_dir': './output'}}
    """
    if args is None:
        args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    cli_dict = {}
    i = 0
    
    while i < len(args):
        if args[i].startswith('--'):
            key = args[i][2:]  # Remove --
            i += 1
            
            # Check if this key has subkey=value pairs
            subdict = {}
            has_subkeys = False
            
            # Collect all following arguments until next -- or end
            while i < len(args) and not args[i].startswith('--'):
                current_arg = args[i]
                
                if '=' in current_arg:
                    # This is a subkey=value pair
                    subkey, value = current_arg.split('=', 1)
                    
                    # Handle nested keys with dots
                    if '.' in subkey:
                        parts = subkey.split('.')
                        current = subdict
                        for part in parts[:-1]:
                            if part not in current:
                                current[part] = {}
                            current = current[part]
                        current[parts[-1]] = _parse_value(value)
                    else:
                        subdict[subkey] = _parse_value(value)
                    has_subkeys = True
                else:
                    # If no subkeys found yet, treat as direct value
                    if not has_subkeys:
                        cli_dict[key] = _parse_value(current_arg)
                        i += 1
                        break
                    # Otherwise, ignore non-key=value arguments after subkeys
                i += 1
            
            # If we collected subkeys, merge with existing key if it exists
            if has_subkeys:
                if key in cli_dict and isinstance(cli_dict[key], dict):
                    # Merge with existing dictionary
                    cli_dict[key].update(subdict)
                else:
                    cli_dict[key] = subdict
            elif key not in cli_dict:
                # Key was specified without value
                cli_dict[key] = True
        else:
            # Skip arguments that don't start with --
            i += 1
    
    return cli_dict


def parse_hybrid_arguments(inputfile: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Parse arguments supporting both legacy and modern formats.
    
    Legacy format: python -m module config.yml "{'key': 'value'}"
    Modern format: python -m module config.yml --key value --key2 subkey=value
    
    Args:
        inputfile: Optional input file path
        
    Returns:
        Tuple of (inputfile, config_dict)
    """
    import os
    
    # Detect if running under pytest
    is_pytest = any("pytest" in arg or "_pytest" in arg for arg in sys.argv[0:2])
    
    # Handle input file
    if len(sys.argv) > 1:
        if inputfile is not None:
            # If running under pytest, skip sys.argv processing since inputfile is provided
            if is_pytest:
                pass  # Use the provided inputfile, ignore sys.argv
            else:
                raise Exception(
                    "2 Input files provided via arguments & function. "
                    "Please provide only 1 file ... FAIL"
                )
        elif not is_pytest:
            # Only use sys.argv[1] when NOT running under pytest
            # Check if first argument is a file
            if os.path.isfile(sys.argv[1]):
                inputfile = sys.argv[1]
            elif not sys.argv[1].startswith('--'):
                raise FileNotFoundError(f"Input file {sys.argv[1]} not found ... FAIL")
    
    # Parse configuration arguments
    cfg_argv_dict = {}
    
    if len(sys.argv) > 2:
        # Check if using old dictionary format
        arg2 = sys.argv[2]
        if arg2.strip().startswith("{") and arg2.strip().endswith("}"):
            # Legacy format: parse as Python dictionary
            try:
                cfg_argv_dict = eval(arg2)
                if not isinstance(cfg_argv_dict, dict):
                    raise ValueError("Not a dictionary")
            except Exception as e:
                raise ValueError(
                    f"Check dictionary format provided in {arg2} ... FAIL. Error: {e}"
                )
        else:
            # Modern format: parse CLI arguments
            cfg_argv_dict = parse_cli_arguments(sys.argv[2:])
    
    # Validate input file exists
    if inputfile and not os.path.isfile(inputfile):
        raise FileNotFoundError(f"Input file {inputfile} not found ... FAIL")
    
    return inputfile, cfg_argv_dict


def _parse_value(value: str) -> Any:
    """
    Parse a string value to appropriate Python type.
    
    Args:
        value: String value to parse
        
    Returns:
        Parsed value (str, int, float, bool, or original string)
    """
    # Remove quotes if present
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    
    # Check for boolean
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return False
    
    # Check for None
    if value.lower() == 'none':
        return None
    
    # Try to parse as number
    try:
        if '.' in value or 'e' in value.lower():
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass
    
    # Return as string
    return value


def merge_cli_with_config(config: Dict[str, Any], cli_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge CLI arguments with configuration, with CLI taking precedence.
    
    Args:
        config: Base configuration dictionary
        cli_args: CLI arguments dictionary
        
    Returns:
        Merged configuration
    """
    from assetutilities.common.update_deep import update_deep_dictionary
    
    return update_deep_dictionary(config, cli_args)


# Convenience function for backward compatibility
def parse_modern_cli_args(args: List[str]) -> Dict[str, Any]:
    """
    Legacy function name for compatibility.
    Delegates to parse_cli_arguments.
    """
    return parse_cli_arguments(args)