# UV Environment Setup for AssetUtilities

This document describes how to use UV (the fast Python package manager) with the AssetUtilities project.

## Quick Start

UV has been configured for this project with all dependencies and parallel processing features.

### Activate Environment and Run Commands

```bash
# Install dependencies and create virtual environment
uv sync

# Install with development dependencies
uv sync --extra dev

# Run Python commands in the UV environment
uv run python your_script.py

# Run the AssetUtilities engine
uv run python -m assetutilities your_config.yml

# Run tests
uv run pytest

# Run linting
uv run ruff check src/

# Run formatting
uv run ruff format src/
```

### Running Parallel Processing

The 30-worker parallel processing is fully supported:

```bash
# Test parallel zip utilities
uv run python -c "
from src.assetutilities.modules.zip_utilities.zip_utilities import ZipUtilities
print('Parallel processing with 30 workers ready!')
"
```

## Environment Details

### Python Version
- **Requirement**: Python >=3.9 (updated from 3.8 for scrapy compatibility)
- **Current**: Python 3.13.5 (managed by UV)

### Dependencies Structure

#### Core Dependencies (Production)
All production dependencies are defined in `pyproject.toml`:
- Data processing: numpy, pandas, sympy
- Visualization: plotly, matplotlib  
- File formats: openpyxl, python-docx, PyPDF2
- Web scraping: scrapy, selenium, playwright
- Parallel processing: Built-in concurrent.futures
- And more...

#### Development Dependencies
Development tools are in the `[project.optional-dependencies]` section:
- build, twine (packaging)
- bumpver (version management)
- pytest (testing)
- ruff (linting and formatting)

### Configuration Files

#### `pyproject.toml`
- Modern Python project configuration
- All dependencies defined in standard format
- UV-compatible structure
- Parallel processing configuration in base configs

#### `uv.lock`
- Exact version lock file created by UV
- Ensures reproducible installations
- Cross-platform compatibility
- Commit this file to version control

#### `.uvrc`
- UV environment configuration
- Performance optimizations
- Managed Python settings

## UV vs Other Tools

### UV Advantages
- **Speed**: 10-100x faster than pip
- **Reliability**: Better dependency resolution
- **Modern**: Uses Rust for performance  
- **Compatibility**: Works with existing Python packaging standards

### Migration from pip/conda
```bash
# Old way
pip install -r requirements.txt

# New way (automatic)
uv sync
```

## Parallel Processing with UV

The AssetUtilities parallel processing features work seamlessly with UV:

### Configuration
Base configuration in `src/assetutilities/base_configs/modules/zip_utilities/zip_utilities.yml`:
```yaml
parallel_processing:
  enabled: true
  max_workers: 30
  timeout_per_file: 3600
  save_error_reports: false
  progress_reporting: true
```

### Performance
- **30 concurrent workers** for zip operations
- **Intelligent worker scaling** based on workload
- **Memory efficient** through process isolation
- **Cross-platform** compatibility

## Development Workflow

### Daily Development
```bash
# Start development
uv sync --extra dev

# Run tests before commits
uv run pytest

# Check code quality
uv run ruff check src/
uv run ruff format src/

# Run your application
uv run python your_script.py
```

### Adding Dependencies
```bash
# Add a production dependency
uv add package-name

# Add a development dependency  
uv add --dev package-name

# Add with version constraints
uv add "package-name>=1.0,<2.0"
```

### Building and Publishing
```bash
# Build package
uv run python -m build

# Publish to PyPI (after configuring credentials)
uv run twine upload dist/*
```

## Troubleshooting

### Common Issues

#### 1. ImportError with wrapt
**Issue**: `ModuleNotFoundError: No module named 'wrapt.wrappers'`
**Solution**: This is a warning from `python-certifi-win32` and doesn't affect functionality. The packages still work correctly.

#### 2. Link Mode Warnings
**Issue**: `Failed to hardlink files; falling back to full copy`
**Solution**: This is expected on different filesystems. Set `UV_LINK_MODE=copy` in environment or use `--link-mode=copy`.

#### 3. Permission Errors
**Issue**: `Access is denied` when creating virtual environment
**Solution**: Make sure no Python processes are using the `.venv` directory, then use `uv venv --clear`.

### Performance Optimization

#### Environment Variables
```bash
# Optimize for performance
export UV_LINK_MODE=copy
export UV_MANAGED_PYTHON=true
export UV_NO_PROGRESS=false
```

#### Cache Management
```bash
# Clear UV cache if needed
uv cache clean

# Show cache info
uv cache dir
```

## Integration with IDEs

### VS Code
Add to `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": ".venv/Scripts/python.exe",
  "python.terminal.activateEnvironment": true
}
```

### PyCharm
1. File → Settings → Project Interpreter
2. Select "Existing environment"
3. Point to `.venv/Scripts/python.exe`

## CI/CD Integration

### GitHub Actions
```yaml
- name: Set up Python and UV
  uses: actions/setup-python@v4
  with:
    python-version: "3.9"
    
- name: Install UV
  run: pip install uv

- name: Install dependencies
  run: uv sync --extra dev

- name: Run tests
  run: uv run pytest
```

## Summary

UV provides a fast, reliable Python environment for AssetUtilities with:
- ✅ **30-worker parallel processing** fully supported
- ✅ **All dependencies** properly resolved and installed
- ✅ **Development tools** integrated (pytest, ruff, etc.)
- ✅ **Cross-platform** compatibility
- ✅ **Modern Python packaging** standards

The environment is ready for high-performance parallel processing and all AssetUtilities functionality.