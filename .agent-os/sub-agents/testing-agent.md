# Testing Agent Configuration

> Repository: AssetUtilities
> Created: 2025-07-31
> Version: 1.0.0

## Agent Purpose

This testing agent provides automated test execution and validation using pytest framework specifically optimized for AssetUtilities Python library testing, focusing on business utility validation, data processing verification, and comprehensive test coverage.

## Testing Framework Integration

### Pytest Configuration
- **Test Discovery**: Automatic discovery of tests in `tests/` directory
- **Test Organization**: Modular test structure matching source code organization
- **Configuration Files**: YAML-based test configurations for data-driven testing
- **Fixtures**: Shared test fixtures for common test data and utilities

### Test Structure
```
tests/
├── __init__.py
├── modules/
│   ├── excel_utilities/
│   │   ├── test_excel_operations.py
│   │   └── excel_test_config.yml
│   ├── visualization/
│   │   ├── test_plotly_charts.py
│   │   └── visualization_test_config.yml
│   └── file_management/
│       ├── test_file_operations.py
│       └── file_management_config.yml
└── integration/
    └── test_workflow_integration.py
```

## Test Execution Patterns

### Unit Testing
- **Scope**: Individual utility functions and classes
- **Focus**: Business logic validation, edge case handling
- **Data**: Use YAML configuration files for test parameters
- **Assertions**: Verify correct data transformations and outputs

### Integration Testing
- **Scope**: Multi-module workflows and utility combinations
- **Focus**: End-to-end business process validation
- **Data**: Real-world data samples and scenarios
- **Performance**: Validate performance with representative datasets

### Validation Testing
- **Scope**: Data quality and business rule compliance
- **Focus**: Excel operations, visualization accuracy, file processing
- **Coverage**: Comprehensive testing of utility edge cases
- **Regression**: Prevent regression in existing functionality

## Test Automation Scripts

### Local Test Execution
```bash
#!/bin/bash
# Run all tests with coverage
pytest tests/ --cov=src/assetutilities --cov-report=html

# Run specific module tests
pytest tests/modules/excel_utilities/ -v

# Run tests with configuration
pytest tests/ --tb=short --durations=10
```

### Continuous Testing
```bash
#!/bin/bash
# Watch for changes and run tests
pytest-watch tests/ src/

# Run tests on file changes
find src/ -name "*.py" | entr pytest tests/
```

## Test Data Management

### YAML Configuration Files
```yaml
# Example test configuration
test_excel_operations:
  input_file: "test_data.xlsx"
  expected_columns: ["A", "B", "C"]
  expected_rows: 100
  transformations:
    - type: "filter"
      column: "A"
      condition: "> 0"
    - type: "aggregate"
      column: "B"
      method: "sum"
```

### Test Data Generation
- **Synthetic Data**: Generate test data for various scenarios
- **Real Data Samples**: Use anonymized real-world data samples
- **Edge Cases**: Create specific test cases for boundary conditions
- **Performance Data**: Large datasets for performance testing

## Validation Procedures

### Data Processing Validation
1. **Input Validation**: Verify correct handling of various input formats
2. **Transformation Accuracy**: Validate data transformation correctness
3. **Output Format**: Ensure outputs match expected formats and schemas
4. **Error Handling**: Test error conditions and recovery mechanisms

### Excel Utilities Validation
1. **File Reading**: Test reading various Excel formats and structures
2. **Data Writing**: Validate Excel file creation and formatting
3. **Cross-Reference**: Test workbook cross-referencing functionality
4. **Performance**: Validate performance with large Excel files

### Visualization Validation
1. **Chart Generation**: Verify correct chart creation and formatting
2. **Data Accuracy**: Validate data representation in visualizations
3. **Interactive Features**: Test plotly interactive chart functionality
4. **Export Formats**: Validate chart export to various formats

## Test Coverage Requirements

### Coverage Targets
- **Unit Tests**: 90%+ coverage for utility functions
- **Integration Tests**: 80%+ coverage for workflow combinations
- **Edge Cases**: 100% coverage for critical business logic
- **Error Handling**: Complete coverage of exception paths

### Coverage Monitoring
```python
# Generate coverage report
pytest --cov=src/assetutilities --cov-report=html --cov-report=term

# Check coverage thresholds
pytest --cov=src/assetutilities --cov-fail-under=90
```

## Performance Testing

### Performance Benchmarks
- **Large Dataset Processing**: Test with datasets > 100MB
- **Excel File Operations**: Benchmark Excel read/write operations
- **Visualization Rendering**: Measure chart generation performance
- **Memory Usage**: Monitor memory consumption during operations

### Performance Test Examples
```python
import pytest
import time
import psutil
import pandas as pd

def test_large_dataset_performance():
    """Test performance with large datasets."""
    # Generate large test dataset
    large_df = pd.DataFrame({
        'col1': range(1000000),
        'col2': range(1000000)
    })
    
    # Measure processing time
    start_time = time.time()
    result = process_large_dataset(large_df)
    execution_time = time.time() - start_time
    
    # Assert performance requirements
    assert execution_time < 10.0  # Should complete in under 10 seconds
    assert len(result) == 1000000
```

## Error Handling Testing

### Exception Testing
- **Invalid Inputs**: Test behavior with malformed or invalid data
- **File Access**: Test file permission and access error handling
- **Network Issues**: Test web scraping error conditions
- **Memory Limits**: Test behavior with insufficient memory

### Recovery Testing
- **Partial Failures**: Test recovery from partial processing failures
- **Data Corruption**: Test handling of corrupted input files
- **Resource Exhaustion**: Test behavior when system resources are limited
- **Timeout Handling**: Test long-running operation timeouts

## Test Reporting

### Test Results
- **HTML Reports**: Generate detailed HTML test reports
- **Coverage Reports**: Comprehensive coverage analysis
- **Performance Reports**: Performance benchmark results
- **Failed Test Analysis**: Detailed failure analysis and debugging info

### Continuous Integration
- **Automated Testing**: Run tests on every commit
- **Test Status**: Report test status to development team
- **Regression Detection**: Identify and alert on regressions
- **Quality Gates**: Prevent merging code with failing tests

## Team Synchronization

### Shared Test Standards
- **Test Naming**: Consistent test naming conventions
- **Configuration Format**: Standardized YAML configuration structure
- **Assertion Patterns**: Common assertion patterns and utilities
- **Mock Usage**: Shared mocking strategies for external dependencies

### Test Environment Management
- **Virtual Environments**: Isolated test environments for each developer
- **Dependency Versions**: Synchronized test dependency versions
- **Test Data**: Shared test data repositories and management
- **CI/CD Integration**: Consistent testing across development environments