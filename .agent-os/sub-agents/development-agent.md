# Development Agent Configuration

> Repository: AssetUtilities
> Created: 2025-07-31
> Version: 1.0.0

## Agent Purpose

This development agent provides code generation and development workflows specifically optimized for AssetUtilities Python library development, focusing on business automation utilities, data processing components, and visualization tools.

## Development Patterns

### Python Package Development
- **Package Structure**: Follow setuptools-based package structure with `src/assetutilities/` layout
- **Module Organization**: Group related utilities (excel_utilities, visualization, file_management, etc.)
- **Code Style**: Use ruff for linting with 88-character line length, double quotes, 4-space indentation
- **Dependency Management**: Use poetry/uv for dependency management, maintain pyproject.toml

### Business Utility Development
- **API Design**: Create consistent, intuitive APIs for business automation tasks
- **Error Handling**: Implement comprehensive error handling for edge cases
- **Configuration**: Use YAML configuration files for utility parameters
- **Documentation**: Include docstrings and usage examples for all public functions

### Data Processing Workflows
- **DataFrame Operations**: Leverage pandas for data manipulation and processing
- **Excel Integration**: Use openpyxl and xlsxwriter for Excel file operations
- **Visualization**: Integrate plotly and matplotlib for business charts and reporting
- **File Management**: Implement robust file operations with proper error handling

## Code Generation Guidelines

### Utility Function Template
```python
def utility_function(input_data, config=None):
    """
    Brief description of utility function.
    
    Args:
        input_data: Description of input parameter
        config: Optional configuration dictionary
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: Description of when this is raised
    """
    # Implementation here
    pass
```

### Module Structure Template
```python
"""
Module description.

This module provides utilities for [specific business function].
"""

from typing import Dict, List, Optional
import pandas as pd
from ..common import utilities

class UtilityClass:
    """Class for [specific utility functionality]."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process data according to business rules."""
        # Implementation
        return data
```

## Testing Integration

### Test Structure
- **Location**: Place tests in `tests/modules/[module_name]/`
- **Naming**: Use `test_[functionality].py` format
- **Configuration**: Use YAML files for test configurations
- **Coverage**: Aim for comprehensive test coverage of business logic

### Test Template
```python
import pytest
import pandas as pd
from assetutilities.modules.utility_module import UtilityClass

class TestUtilityClass:
    """Test cases for UtilityClass."""
    
    def test_basic_functionality(self):
        """Test basic utility functionality."""
        # Arrange
        utility = UtilityClass()
        test_data = pd.DataFrame({'col1': [1, 2, 3]})
        
        # Act
        result = utility.process(test_data)
        
        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
```

## Development Environment Setup

### Local Development
1. **Clone Repository**: `git clone [repository_url]`
2. **Install Dependencies**: `poetry install` or `uv sync`
3. **Activate Environment**: `poetry shell` or `source .venv/bin/activate`
4. **Run Tests**: `pytest tests/`
5. **Code Quality**: `ruff check src/` and `ruff format src/`

### Development Workflow
1. **Branch Creation**: Create feature branches from main
2. **Development**: Follow TDD approach - write tests first
3. **Code Quality**: Run ruff checks before committing
4. **Testing**: Ensure all tests pass locally
5. **Documentation**: Update relevant documentation

## Integration Points

### Common Modules
- **ApplicationManager**: Use for coordinating multiple utilities
- **data.py**: Leverage for data structure management
- **visualization.py**: Use for consistent chart generation
- **yml_utilities.py**: Use for configuration management

### External Dependencies
- **pandas**: Primary data processing library
- **plotly/matplotlib**: Visualization libraries
- **openpyxl**: Excel file operations
- **PyYAML**: Configuration file processing

## Collaboration Guidelines

### Code Reviews
- **Focus**: Business logic correctness, error handling, documentation
- **Performance**: Consider performance implications for large datasets
- **API Consistency**: Ensure new utilities follow established patterns
- **Testing**: Verify comprehensive test coverage

### Team Synchronization
- **Shared Standards**: Follow established code style and patterns
- **Configuration**: Use shared YAML configurations for consistency
- **Documentation**: Maintain up-to-date module documentation
- **Dependencies**: Coordinate dependency updates across team