#!/usr/bin/env python
"""
Standalone script to propagate slash commands from AssetUtilities to other repositories.
This script can be run from any directory.
"""

import sys
from pathlib import Path

# Add the assetutilities commands directory to Python path
ASSETUTILITIES_DIR = Path(__file__).parent
sys.path.insert(0, str(ASSETUTILITIES_DIR / ".agent-os/commands"))

# Import the propagate_commands module
try:
    import propagate_commands
except ImportError:
    print("❌ Could not import propagate_commands module")
    print(f"   Looked in: {ASSETUTILITIES_DIR / '.agent-os/commands'}")
    sys.exit(1)

def main():
    """Run the propagate commands with proper paths."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Propagate AssetUtilities slash commands to other repositories"
    )
    parser.add_argument(
        "--target-dir", 
        default="/mnt/github/github",
        help="Directory containing target repositories (default: /mnt/github/github)"
    )
    parser.add_argument(
        "--parallel", 
        type=int, 
        default=5,
        help="Number of parallel workers (default: 5)"
    )
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Force overwrite existing files"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--repos", 
        nargs="+",
        help="Specific repositories to target"
    )
    parser.add_argument(
        "--commands", 
        nargs="+",
        help="Specific commands to propagate (default: all)"
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Propagating from: {ASSETUTILITIES_DIR}")
    print(f"📍 Target directory: {args.target_dir}")
    
    # Call the main function from propagate_commands
    return propagate_commands.main(
        source=str(ASSETUTILITIES_DIR),
        target_dir=args.target_dir,
        commands=args.commands,
        parallel=args.parallel,
        force=args.force,
        dry_run=args.dry_run,
        repos=args.repos
    )

if __name__ == "__main__":
    sys.exit(main())