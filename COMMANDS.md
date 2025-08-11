# AssetUtilities Slash Commands

Custom slash commands for repository management and automation.

## Quick Start

```bash
# List all available commands
./slash_commands.py --list

# Run a specific command
./slash_commands.py /modernize-deps

# Get help for a command
./slash_commands.py /modernize-deps --help
```

## Available Commands

### `/modernize-deps`

**Purpose**: Modernize dependency management across Python repositories by consolidating all requirements into `pyproject.toml` and setting up UV environment configuration.

**Features**:
- Consolidates multiple requirements*.txt files into pyproject.toml
- Creates UV environment configuration (uv.toml)
- Sets up Python version management (.python-version)
- Enables parallel processing configuration
- Creates setup scripts for easy environment setup
- Removes redundant requirement files

**Usage**:
```bash
# Modernize current directory
./slash_commands.py /modernize-deps

# Process specific repositories
./slash_commands.py /modernize-deps --repos repo1 repo2 repo3

# Use more parallel workers
./slash_commands.py /modernize-deps --parallel=10

# Dry run to see what would be done
./slash_commands.py /modernize-deps --dry-run

# Skip backup creation
./slash_commands.py /modernize-deps --no-backup
```

**What it does**:
1. Scans for all requirements files in each repository
2. Consolidates dependencies into organized pyproject.toml sections
3. Creates UV configuration for single environment management
4. Sets up Python 3.11 as default version
5. Creates setup_uv_env.sh for easy environment initialization
6. Cleans up redundant requirements files
7. Validates the installation

### `/propagate-commands`

**Purpose**: Distribute slash commands from this repository to all other repositories in a directory, ensuring consistent tooling across your entire codebase.

**Features**:
- Discovers all custom commands in source repository
- Creates standardized command structure in target repos
- Installs command files with proper organization
- Maintains command registry for tracking
- Creates documentation for installed commands
- Validates installation success

**Usage**:
```bash
# Propagate all commands to sibling repositories
./slash_commands.py /propagate-commands

# Propagate specific commands only
./slash_commands.py /propagate-commands --commands /modernize-deps

# Target specific directory
./slash_commands.py /propagate-commands --target-dir /mnt/github/github

# Force overwrite existing commands
./slash_commands.py /propagate-commands --force

# Dry run to see what would be propagated
./slash_commands.py /propagate-commands --dry-run

# Target specific repositories
./slash_commands.py /propagate-commands --repos datascience digitalmodel
```

**What it does**:
1. Discovers commands in `.agent-os/commands/` directory
2. Creates command structure in target repositories
3. Copies command files to standardized locations
4. Creates command wrapper (slash_commands.py) in each repo
5. Maintains command registry for version tracking
6. Generates documentation (COMMANDS.md)
7. Validates successful installation

## Command Structure

Commands are organized in the following structure:

```
assetutilities/
├── .agent-os/
│   └── commands/           # Command implementations
│       ├── __init__.py
│       ├── modernize_deps.py
│       └── propagate_commands.py
├── .command-registry.json  # Command metadata and registry
├── slash_commands.py       # Main command wrapper
└── COMMANDS.md            # This documentation
```

## Adding New Commands

To add a new slash command:

1. Create a Python file in `.agent-os/commands/` directory
2. Name it using underscores (e.g., `my_new_command.py`)
3. Include a docstring with the command name (e.g., `/my-new-command`)
4. Implement a `main()` function that accepts arguments
5. Update `.command-registry.json` with command metadata
6. Use `/propagate-commands` to distribute to other repos

### Command Template

```python
#!/usr/bin/env python
"""
/my-command - Brief description of what the command does

Detailed description of the command's purpose and functionality.
"""

import argparse
import sys

def main():
    """Main entry point for the command."""
    parser = argparse.ArgumentParser(description="My command description")
    parser.add_argument("--option", help="An option")
    
    args = parser.parse_args()
    
    # Command implementation here
    print("Executing my-command...")
    
    return 0  # Return 0 for success, non-zero for failure

if __name__ == "__main__":
    sys.exit(main())
```

## Parallel Processing

Both commands support parallel processing for improved performance:

- **Default**: 5 parallel workers
- **Configurable**: Use `--parallel=N` to adjust
- **Benefits**: Significantly faster when processing multiple repositories

## Environment Requirements

- Python 3.9 or higher
- UV package manager (for /modernize-deps)
- Git (for repository detection)
- Write permissions to target repositories

## Best Practices

1. **Always use dry-run first**: Test commands with `--dry-run` before actual execution
2. **Keep backups**: Don't use `--no-backup` unless you're certain
3. **Start small**: Test on a few repositories before running on all
4. **Check logs**: Review output for any errors or warnings
5. **Validate results**: Ensure commands completed successfully

## Troubleshooting

### Command not found
- Ensure the command file exists in `.agent-os/commands/`
- Check that the command is registered in `.command-registry.json`
- Verify the command name matches the file name pattern

### Permission errors
- Ensure you have write permissions to target repositories
- Check that files aren't locked by other processes

### Import errors
- Verify Python version is 3.9 or higher
- Install required dependencies from pyproject.toml

## Integration with Agent OS

These commands are designed to work with the Agent OS framework:

- Commands follow Agent OS naming conventions
- Integration with `.agent-os/` directory structure
- Compatible with Agent OS workflow automation
- Support for cross-repository operations

## Contributing

To contribute new commands:

1. Follow the command template structure
2. Include comprehensive help documentation
3. Add appropriate error handling
4. Update command registry and documentation
5. Test thoroughly before propagating

## License

Part of AssetUtilities - MIT License