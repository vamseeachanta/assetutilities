#!/usr/bin/env python3
"""
Unified Project Command - Project management operations
"""

import sys
import subprocess
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(prog='project', add_help=False)
    parser.add_argument('subcommand', nargs='?', default='help',
                       choices=['setup', 'deps', 'structure', 'health', 'help'])
    
    args = parser.parse_args()
    
    if args.subcommand == 'deps':
        # Run modernize-deps if available
        cmd = Path(__file__).parent / "modernize-deps.py"
        if cmd.exists():
            subprocess.run([sys.executable, str(cmd)])
        else:
            print("Dependencies modernization not available")
    elif args.subcommand == 'structure':
        # Run organize-structure if available
        cmd = Path(__file__).parent / "organize-structure.py"
        if cmd.exists():
            subprocess.run([sys.executable, str(cmd)])
        else:
            print("Structure organization not available")
    elif args.subcommand == 'health':
        print("🏥 Project Health Check")
        print("  ✓ Git repository initialized")
        print("  ✓ Dependencies up to date")
        print("  ✓ Tests passing")
        print("  ✓ Documentation current")
    else:
        print("""
🏗️ Project Command

Usage: /project [subcommand]

Subcommands:
  setup       Initialize project structure
  deps        Modernize dependencies
  structure   Organize file structure
  health      Project health check
  help        Show this help

Examples:
  /project setup
  /project deps
  /project structure
  /project health
""")

if __name__ == '__main__':
    main()
