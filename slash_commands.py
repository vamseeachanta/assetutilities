#!/usr/bin/env python
"""
Slash Command Wrapper for AssetUtilities
Provides a unified interface for all custom slash commands.
"""

import sys
import os
from pathlib import Path
import importlib.util
import argparse

# Add command directory to path
COMMAND_DIR = Path(__file__).parent / ".agent-os/commands"
sys.path.insert(0, str(COMMAND_DIR))

def load_command(command_name: str):
    """Dynamically load a command module."""
    # Remove leading slash and convert to module name
    module_name = command_name.lstrip('/').replace('-', '_')
    module_path = COMMAND_DIR / f"{module_name}.py"
    
    if not module_path.exists():
        print(f"❌ Command {command_name} not found!")
        print(f"   Looked for: {module_path}")
        return None
    
    # Load the module
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    
    return None

def list_available_commands():
    """List all available commands."""
    print("📋 Available Slash Commands in AssetUtilities:")
    print("=" * 50)
    
    commands = {
        "/modernize-deps": "Modernize dependency management across repositories",
        "/propagate-commands": "Distribute slash commands to other repositories",
        "/git-trunk-flow": "Complete git workflow with trunk-based development best practices",
        "/sync-all-commands": "Bidirectional sync of slash commands from all repos to master",
        "/install-ecosystem-awareness": "Add slash command suggestions to all AI agents"
    }
    
    # Load command registry if exists
    registry_file = Path(__file__).parent / ".command-registry.json"
    if registry_file.exists():
        import json
        with open(registry_file, 'r') as f:
            registry = json.load(f)
            commands.update({
                cmd: info.get('description', 'No description')
                for cmd, info in registry.get("commands", {}).items()
            })
    
    # Also scan command directory
    if COMMAND_DIR.exists():
        for py_file in sorted(COMMAND_DIR.glob("*.py")):
            if py_file.name != "__init__.py":
                cmd_name = "/" + py_file.stem.replace('_', '-')
                if cmd_name not in commands:
                    # Try to extract description from file
                    try:
                        content = py_file.read_text()
                        lines = content.split('\n')
                        for line in lines:
                            if line.strip() and not line.startswith('#'):
                                commands[cmd_name] = "Custom slash command"
                                break
                    except:
                        commands[cmd_name] = "Custom slash command"
    
    # Display commands
    for cmd, desc in sorted(commands.items()):
        print(f"  {cmd:<25} - {desc}")
    
    print("\n" + "=" * 50)
    print("Usage Examples:")
    print("  ./slash_commands.py /modernize-deps")
    print("  ./slash_commands.py /propagate-commands --source=.")
    print("  ./slash_commands.py --list")
    print("\nFor help on a specific command:")
    print("  ./slash_commands.py /command-name --help")

def main():
    """Main entry point for slash commands."""
    if len(sys.argv) < 2:
        list_available_commands()
        sys.exit(0)
    
    command = sys.argv[1]
    
    # Special case: list commands
    if command in ["--list", "-l", "list"]:
        list_available_commands()
        sys.exit(0)
    
    # Handle help for listing
    if command in ["--help", "-h", "help"]:
        print("AssetUtilities Slash Commands")
        print("\nUsage: ./slash_commands.py <command> [options]")
        print("\nUse --list to see all available commands")
        sys.exit(0)
    
    # Load and execute command
    module = load_command(command)
    if module:
        # Check if module has a main function
        if hasattr(module, 'main'):
            # Pass remaining arguments to the command
            # Reconstruct sys.argv for the module
            original_argv = sys.argv.copy()
            sys.argv = [command] + sys.argv[2:]
            
            try:
                result = module.main()
                sys.exit(result if result is not None else 0)
            except KeyboardInterrupt:
                print("\n⚠️  Command interrupted by user")
                sys.exit(130)
            except Exception as e:
                print(f"❌ Error executing {command}: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            print(f"❌ Command {command} does not have a main() function!")
            sys.exit(1)
    else:
        print(f"❌ Unknown command: {command}")
        print("\nAvailable commands:")
        list_available_commands()
        sys.exit(1)

if __name__ == "__main__":
    main()