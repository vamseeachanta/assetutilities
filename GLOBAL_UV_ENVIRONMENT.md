# Global UV Environment Setup for AssetUtilities

> **Status:** ✅ **ACTIVE**  
> **Environment Path:** `%USERPROFILE%\.uv\envs\assetutilities-global`  
> **Python Version:** 3.13.5  
> **Total Packages:** 111 packages installed  

## Overview

This document describes how to use the AssetUtilities UV environment globally across multiple repositories. The global environment contains all AssetUtilities dependencies and development tools, making it available for use in any project without reinstalling packages.

## ✅ Environment Setup Complete

The global AssetUtilities environment has been successfully created with:

- **Location:** `%USERPROFILE%\.uv\envs\assetutilities-global` (Windows) / `$HOME/.uv/envs/assetutilities-global` (Unix)
- **Python:** 3.13.5
- **AssetUtilities:** Installed in development mode from `D:\github\assetutilities`
- **All Dependencies:** 111 packages including pandas, plotly, scrapy, selenium, etc.

## Usage Methods

### Method 1: Copy Activation Scripts (Recommended)

**For Windows:**
1. Copy `scripts/activate-assetutils-global.bat` to your target repository
2. Run the script: `activate-assetutils-global.bat`
3. The environment will be activated with all AssetUtilities tools available

**For Unix/Linux/macOS:**
1. Copy `scripts/activate-assetutils-global.sh` to your target repository
2. Make it executable: `chmod +x activate-assetutils-global.sh`
3. Run: `source activate-assetutils-global.sh`

### Method 2: Direct UV Commands

**Windows:**
```cmd
# Activate the global environment
call "%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\activate.bat"

# Or run commands directly
uv run --python "%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe" your_script.py
```

**Unix/Linux/macOS:**
```bash
# Activate the global environment
source "$HOME/.uv/envs/assetutilities-global/bin/activate"

# Or run commands directly
uv run --python "$HOME/.uv/envs/assetutilities-global/bin/python" your_script.py
```

### Method 3: Environment Variable Setup

Add to your shell profile (`.bashrc`, `.zshrc`, etc.) or Windows environment variables:

**Windows:**
```cmd
set ASSETUTILS_PYTHON=%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe
```

**Unix:**
```bash
export ASSETUTILS_PYTHON="$HOME/.uv/envs/assetutilities-global/bin/python"
```

Then use: `python "$ASSETUTILS_PYTHON" your_script.py`

## Available Tools and Libraries

The global environment includes:

### Core AssetUtilities Modules
- **Excel Utilities:** openpyxl, xlsxwriter, excel2img
- **Data Processing:** pandas, numpy
- **Visualization:** plotly, matplotlib
- **File Management:** All built-in file utilities
- **Web Scraping:** scrapy, selenium, playwright, beautifulsoup4
- **Document Processing:** python-docx, PyPDF2
- **YAML Processing:** PyYAML, ruamel.yaml

### Development Tools
- **Testing:** pytest
- **Code Quality:** ruff (linting and formatting)
- **Build Tools:** build, twine, setuptools
- **Version Management:** bumpver

### Additional Utilities
- **Git Integration:** gitpython
- **Web Requests:** requests, fake_headers
- **Automation:** undetected-chromedriver
- **Logging:** loguru
- **Template Engine:** jinja2

## Repository Integration Examples

### Example 1: Data Analysis Project

```python
# your_project/analysis.py
from assetutilities.modules.data_exploration import df_basic_statistics
from assetutilities.modules.visualization import plotly_charts
import pandas as pd

# Use AssetUtilities functions directly
df = pd.read_csv('data.csv')
stats = df_basic_statistics.get_statistics(df)
plotly_charts.create_scatter_plot(df, 'x', 'y')
```

Run with: `activate-assetutils-global.bat && python analysis.py`

### Example 2: Excel Processing Project

```python
# your_project/excel_processor.py
from assetutilities.modules.excel_utilities import excel_utilities
from assetutilities.engine import engine

# Load configuration and process Excel files
cfg = engine('config.yml')
excel_utils = excel_utilities.ExcelUtilities(cfg)
excel_utils.process_workbook('input.xlsx')
```

### Example 3: Web Scraping Project

```python
# your_project/scraper.py
from assetutilities.modules.web_scraping import scrapy_utilities
from assetutilities.modules.web_scraping import BeautifulSoup_utilities

# Use built-in scraping utilities
scraper = scrapy_utilities.ScrapyUtilities()
soup_utils = BeautifulSoup_utilities.BeautifulSoupUtilities()
```

## Testing with Global Environment

The global environment includes pytest, so you can run tests directly:

```bash
# Activate environment
activate-assetutils-global.bat  # Windows
source activate-assetutils-global.sh  # Unix

# Run tests
pytest tests/
pytest tests/specific_test.py -v
```

## Maintenance and Updates

### Updating the Global Environment

When AssetUtilities is updated:

1. **Update the source repository:**
   ```bash
   cd D:\github\assetutilities
   git pull origin main
   ```

2. **Reinstall in global environment:**
   ```bash
   uv pip install -e . --python "%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe"
   ```

### Adding New Dependencies

To add packages to the global environment:

```bash
uv pip install new_package --python "%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe"
```

### Recreating the Environment

If you need to recreate the global environment:

1. **Remove existing environment:**
   ```bash
   rm -rf "%USERPROFILE%\.uv\envs\assetutilities-global"  # Windows (in Git Bash)
   rm -rf "$HOME/.uv/envs/assetutilities-global"         # Unix
   ```

2. **Run setup script:**
   ```bash
   # Windows
   scripts\setup-global-env.bat
   
   # Unix
   scripts/setup-global-env.sh
   ```

## Troubleshooting

### Common Issues and Solutions

**Issue:** "Global AssetUtilities environment not found!"
- **Solution:** Run the setup script from the AssetUtilities repository first

**Issue:** Import errors for AssetUtilities modules
- **Solution:** Ensure the global environment is activated or use the direct Python path

**Issue:** Permission denied errors
- **Solution:** Check that scripts are executable (`chmod +x` on Unix systems)

### Environment Verification

To verify the global environment is working correctly:

```python
# Test script: test_global_env.py
try:
    import assetutilities
    from assetutilities.modules.excel_utilities import excel_utilities
    from assetutilities.modules.visualization import plotly_charts
    import pandas as pd
    import plotly.graph_objects as go
    print("✅ Global AssetUtilities environment working correctly!")
    print(f"AssetUtilities version: {assetutilities.__version__}")
except ImportError as e:
    print(f"❌ Import error: {e}")
```

Run with: `python test_global_env.py`

## Performance Considerations

### Benefits
- **No Dependency Conflicts:** Single environment for all AssetUtilities projects
- **Fast Startup:** No package installation time for new projects
- **Consistent Environment:** Same tool versions across all projects
- **Development Efficiency:** Immediate access to all utilities

### Considerations
- **Storage:** ~500MB for complete environment
- **Updates:** Manual update process for environment synchronization
- **Path Management:** Requires proper activation scripts

## Integration with IDEs

### Visual Studio Code
1. Set Python interpreter to: `%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe`
2. Or use workspace settings:
   ```json
   {
     "python.pythonPath": "%USERPROFILE%\\.uv\\envs\\assetutilities-global\\Scripts\\python.exe"
   }
   ```

### PyCharm
1. Go to Settings → Project → Python Interpreter
2. Add existing interpreter: `%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe`

### Jupyter Notebooks
```bash
# Install Jupyter in global environment
uv pip install jupyter --python "%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe"

# Start Jupyter with AssetUtilities available
activate-assetutils-global.bat && jupyter notebook
```

## Summary

The global AssetUtilities UV environment provides:

✅ **Cross-Repository Access** to all AssetUtilities modules  
✅ **111 Pre-installed Packages** including all dependencies  
✅ **Development Tools** (pytest, ruff, build tools)  
✅ **Easy Activation Scripts** for Windows and Unix systems  
✅ **IDE Integration** support  
✅ **Maintenance Scripts** for updates and recreation  

This setup eliminates the need to install AssetUtilities dependencies in each project, providing a consistent development environment across all repositories that use AssetUtilities.