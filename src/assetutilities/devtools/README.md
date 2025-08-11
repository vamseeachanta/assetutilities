# AssetUtilities DevTools

A comprehensive suite of repository management and automation tools that can be used anywhere after installing AssetUtilities.

## Installation

```bash
# Install AssetUtilities with devtools
pip install -e /path/to/assetutilities

# Or install from PyPI (when published)
pip install assetutilities
```

## Available Commands

After installation, you'll have access to these command-line tools from anywhere:

### `assetutils-devtools`

The main command-line interface for all devtools functionality.

```bash
# Show help
assetutils-devtools --help

# Modernize dependencies
assetutils-devtools modernize-deps --target-dir /path/to/repos

# Propagate commands
assetutils-devtools propagate-commands --target-dir /path/to/repos
```

### Command: `modernize-deps`

Modernizes dependency management across Python repositories by consolidating all requirements into `pyproject.toml`.

**Features:**
- Consolidates multiple requirements*.txt files
- Creates UV environment configuration
- Sets up Python version management
- Enables parallel processing
- Creates setup scripts
- Cleans up redundant files

**Usage:**
```bash
# Modernize current directory
assetutils-devtools modernize-deps

# Process specific directory
assetutils-devtools modernize-deps --target-dir /mnt/github/github

# Process specific repositories
assetutils-devtools modernize-deps --repos repo1 repo2 repo3

# Use more parallel workers
assetutils-devtools modernize-deps --parallel 10

# Dry run mode
assetutils-devtools modernize-deps --dry-run

# Skip backup creation
assetutils-devtools modernize-deps --no-backup
```

### Command: `propagate-commands`

Distributes slash commands from a source repository to multiple target repositories.

**Features:**
- Discovers custom commands automatically
- Creates standardized command structure
- Maintains command registry
- Generates documentation
- Validates installation

**Usage:**
```bash
# Propagate from AssetUtilities (auto-detected)
assetutils-devtools propagate-commands --target-dir /mnt/github/github

# Specify source repository
assetutils-devtools propagate-commands --source /path/to/source --target-dir /path/to/repos

# Propagate specific commands
assetutils-devtools propagate-commands --commands /modernize-deps /custom-command

# Force overwrite existing files
assetutils-devtools propagate-commands --force

# Target specific repositories
assetutils-devtools propagate-commands --repos datascience digitalmodel
```

## Python API Usage

You can also use the devtools programmatically in your Python scripts:

```python
from pathlib import Path
from assetutilities.devtools import (
    DependencyModernizer,
    CommandPropagator,
    modernize_repository,
    find_python_repositories,
    find_repositories
)

# Modernize a single repository
repo_path = Path("/path/to/repo")
modernizer = DependencyModernizer(repo_path, backup=True)
report = modernizer.modernize()

# Modernize multiple repositories
base_dir = Path("/mnt/github/github")
repos = find_python_repositories(base_dir)
for repo in repos:
    report = modernize_repository(repo, backup=True)
    print(f"Processed {repo.name}: {report['success']}")

# Propagate commands
source_repo = Path("/path/to/assetutilities")
target_dir = Path("/mnt/github/github")
propagator = CommandPropagator(source_repo, target_dir, force=False)

# Discover available commands
commands = propagator.discover_commands()
print(f"Found commands: {list(commands.keys())}")

# Propagate to a specific repository
repo_path = Path("/path/to/target/repo")
result = propagator.propagate_to_repository(repo_path)
print(f"Installation successful: {result['success']}")
```

## Configuration

### Environment Variables

You can set these environment variables to customize behavior:

```bash
# Default target directory for operations
export ASSETUTILS_TARGET_DIR="/mnt/github/github"

# Default number of parallel workers
export ASSETUTILS_PARALLEL_WORKERS=10

# Default Python version for modernization
export ASSETUTILS_PYTHON_VERSION="3.11"
```

### User Preferences

Create a `.assetutils.yml` file in your home directory:

```yaml
devtools:
  modernize_deps:
    backup: true
    parallel: 10
    python_version: "3.11"
    cleanup_redundant: true
  
  propagate_commands:
    force: false
    parallel: 5
    create_documentation: true
```

## Parallel Processing

Both commands support parallel processing for improved performance:

- **Default**: 5 parallel workers
- **Configurable**: Use `--parallel N` to adjust
- **Automatic**: Detects optimal workers based on CPU cores

## File Structure Created

### For `modernize-deps`:
```
repository/
├── pyproject.toml          # Unified dependencies
├── uv.toml                 # UV configuration
├── .python-version         # Python version specification
├── setup_uv_env.sh         # Setup script
└── requirements.txt        # Compatibility reference
```

### For `propagate-commands`:
```
repository/
├── .agent-os/
│   └── commands/          # Command implementations
│       ├── __init__.py
│       └── *.py           # Individual commands
├── .command-registry.json # Command metadata
├── slash_commands.py      # Command wrapper
└── COMMANDS.md           # Documentation
```

## Integration with CI/CD

You can integrate these tools into your CI/CD pipeline:

```yaml
# GitHub Actions example
name: Modernize Dependencies

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  modernize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install AssetUtilities
        run: pip install assetutilities
      
      - name: Modernize Dependencies
        run: assetutils-devtools modernize-deps --target-dir . --no-backup
      
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          title: "chore: Modernize dependency management"
          commit-message: "chore: Modernize dependencies with AssetUtilities"
          branch: modernize-deps
```

## Troubleshooting

### Command not found
After installation, you may need to:
```bash
# Refresh your shell
source ~/.bashrc  # or ~/.zshrc

# Or ensure pip scripts are in PATH
export PATH="$HOME/.local/bin:$PATH"
```

### Permission errors
```bash
# Install with user flag
pip install --user assetutilities

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install assetutilities
```

### Import errors
Ensure AssetUtilities is properly installed:
```python
import assetutilities.devtools
print(assetutilities.devtools.__version__)
```

## Contributing

To contribute to AssetUtilities DevTools:

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Write tests for new functionality
5. Submit a pull request

## License

Part of AssetUtilities - MIT License