#!/usr/bin/env python3
"""
Universal Slash Command Runner for AssetUtilities

This script allows you to run AssetUtilities slash commands from any directory.
Copy this file anywhere and run it to execute commands.

Usage:
    python run_slash_command.py /modernize-deps --target-dir .
    python run_slash_command.py /propagate-commands --target-dir /path/to/repos
"""

import sys
import os
from pathlib import Path
import subprocess

# Configuration - Update this path if AssetUtilities is in a different location
ASSETUTILITIES_PATH = "/mnt/github/github/assetutilities"

def run_command_in_directory(directory, command, args):
    """Run a slash command in a specific directory."""
    original_dir = os.getcwd()
    
    try:
        # Change to the target directory
        os.chdir(directory)
        
        # Build the command
        cmd = [sys.executable, "./slash_commands.py", command] + args
        
        print(f"📍 Running in: {directory}")
        print(f"🔧 Command: {' '.join(cmd)}")
        print("")
        
        # Run the command
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode
        
    finally:
        # Always return to original directory
        os.chdir(original_dir)

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Universal Slash Command Runner for AssetUtilities")
        print("=" * 50)
        print("\nUsage:")
        print("  python run_slash_command.py <command> [options]")
        print("\nAvailable commands:")
        print("  /modernize-deps      - Modernize dependency management")
        print("  /propagate-commands  - Distribute commands to other repos")
        print("\nExamples:")
        print("  python run_slash_command.py /modernize-deps --target-dir .")
        print("  python run_slash_command.py /propagate-commands --dry-run")
        print(f"\nAssetUtilities location: {ASSETUTILITIES_PATH}")
        return 1
    
    # Get command and arguments
    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Check if AssetUtilities exists
    assetutils_path = Path(ASSETUTILITIES_PATH)
    if not assetutils_path.exists():
        print(f"❌ AssetUtilities not found at: {ASSETUTILITIES_PATH}")
        print("   Please update ASSETUTILITIES_PATH in this script")
        return 1
    
    # Check if slash_commands.py exists
    slash_cmd_path = assetutils_path / "slash_commands.py"
    if not slash_cmd_path.exists():
        print("❌ slash_commands.py not found in AssetUtilities")
        return 1
    
    # Special handling for certain commands
    if command == "/modernize-deps":
        # For modernize-deps, we might want to run it in the current directory
        if "--target-dir" not in ' '.join(args):
            args.extend(["--target-dir", os.getcwd()])
    
    elif command == "/propagate-commands":
        # For propagate-commands, default to /mnt/github/github if not specified
        if "--target-dir" not in ' '.join(args):
            args.extend(["--target-dir", "/mnt/github/github"])
    
    # Run the command
    print("🚀 Running AssetUtilities Slash Command")
    print("=" * 50)
    
    return run_command_in_directory(str(assetutils_path), command, args)

if __name__ == "__main__":
    sys.exit(main())