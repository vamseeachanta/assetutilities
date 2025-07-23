# Technical Stack

> Last Updated: 2025-07-23
> Version: 1.0.0

## Core Technologies

### Application Framework
- **Framework:** Python Package (setuptools)
- **Version:** Python 3.8+
- **Language:** Python 3.8+

### Database
- **Primary:** N/A (utility library)
- **Version:** N/A
- **ORM:** N/A

## Dependencies Stack

### Core Dependencies
- **Configuration:** PyYAML, ruamel.yaml
- **Data Processing:** numpy, pandas
- **Version:** Latest stable versions

### Visualization Libraries
- **Primary:** Plotly (interactive charts)
- **Secondary:** Matplotlib (static charts)
- **Implementation:** Integrated utility wrappers

### Document Processing
- **Excel:** openpyxl, xlsxwriter, excel2img (Windows)
- **PDF:** PyPDF2, tabula
- **Word:** python-docx
- **CSV:** Built-in csv module with chardet encoding detection

### File & Data Utilities
- **File Operations:** Built-in os, pathlib
- **Compression:** Built-in zipfile utilities
- **Web Scraping:** scrapy==2.12, BeautifulSoup4
- **Version Control:** gitpython==3.1.31

### Development & Testing
- **Code Quality:** ruff (linting and formatting)
- **Testing:** pytest
- **Documentation:** PlantUML for diagrams
- **Mathematical:** sympy>=1.13.3

### Web & Browser Automation
- **Browser Testing:** playwright, selenium
- **Request Handling:** fake_headers, undetected-chromedriver
- **HTML Parsing:** parsel

## Infrastructure

### Application Hosting
- **Platform:** PyPI (Python Package Index)
- **Service:** Package distribution
- **Region:** Global CDN distribution

### Database Hosting
- **Provider:** N/A
- **Service:** N/A (utility library)
- **Backups:** N/A

### Asset Storage
- **Provider:** Git repository
- **CDN:** N/A
- **Access:** Public open source

## Deployment

### CI/CD Pipeline
- **Platform:** Manual deployment
- **Trigger:** Version bump with bumpver tool
- **Tests:** pytest test suite

### Package Management
- **Build System:** setuptools>=61.0.0
- **Distribution:** wheel format
- **Publishing:** twine to PyPI

### Environments
- **Production:** PyPI published package
- **Development:** Local pip install -e .
- **Testing:** pytest with coverage

### Version Management
- **Tool:** bumpver
- **Pattern:** MAJOR.MINOR.PATCH (currently 0.0.8)
- **Strategy:** Semantic versioning

## Code Quality Standards

### Linting & Formatting
- **Tool:** ruff
- **Line Length:** 88 characters
- **Target Version:** Python 3.8+
- **Import Sorting:** isort integration

### Code Style
- **Quote Style:** Double quotes
- **Indentation:** Spaces (4 spaces)
- **Line Endings:** Auto-detection
- **Format:** Black-compatible via ruff

### Testing Framework
- **Primary:** pytest
- **Coverage:** Not currently measured
- **Test Data:** YAML configuration files
- **Structure:** tests/ directory with module organization

## Repository Structure
- **Code Repository URL:** https://github.com/vamseeachanta/assetutilities
- **License:** MIT
- **Documentation:** Markdown in docs/ directory
- **Examples:** Extensive test suite demonstrates usage patterns