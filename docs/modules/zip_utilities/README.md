# ZIP Utilities Module

The ZIP Utilities module provides powerful tools for creating ZIP archives from files based on stem patterns. It's designed for high-performance processing of large datasets with parallel processing capabilities.

## Table of Contents

- [Overview](#overview)
- [Configuration Structure](#configuration-structure)
- [Directory Structure Pattern](#directory-structure-pattern)
- [Usage Examples](#usage-examples)
- [Configuration Reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

The ZIP utilities module creates ZIP archives by grouping files based on their stem (common filename prefix). It supports:

- **Stem-based grouping**: Groups files with common prefixes into single ZIP files
- **Parallel processing**: Processes multiple stems simultaneously for high performance
- **Flexible directory structure**: Separates stem directories from files to be zipped
- **Multiple file extensions**: Can process different file types simultaneously

## Configuration Structure

### Required Sections

```yaml
# Basic metadata
library: assetutlities
basename: zip_utilities

# Analysis configuration (defines what files to zip)
analysis:
  flag: True
  type: zip_by_stem
  by: stem
  input_directory: ../output/csv/folder_name  # CSV files to be zipped
  filename:
    extension: [csv]  # File types to include in ZIP

# Analysis settings (required for routing)
analysis_settings:
  flag: True
  type: zip_by_stem
  by: stem

# File management (defines stem source and output)
file_management:
  flag: True
  input_directory: ../folder_name          # YML files for stem extraction
  output_directory: ../output/zip/folder_name  # ZIP output location
  filename:
    extension: [yml]  # Files used for stem names
```

## Directory Structure Pattern

The module uses a three-tier directory structure:

```
project/
├── folder_name/              # Stem directory (YML files)
│   ├── file_stem1.yml
│   ├── file_stem2.yml
│   └── file_stem3.yml
├── output/
│   ├── csv/
│   │   └── folder_name/      # Files to be zipped
│   │       ├── file_stem1_data1.csv
│   │       ├── file_stem1_data2.csv
│   │       ├── file_stem2_data1.csv
│   │       └── file_stem3_data1.csv
│   └── zip/
│       └── folder_name/      # ZIP output directory
│           ├── file_stem1.zip (contains file_stem1_*.csv)
│           ├── file_stem2.zip (contains file_stem2_*.csv)
│           └── file_stem3.zip (contains file_stem3_*.csv)
```

## Usage Examples

### Basic Command Line Usage

```bash
# Using default configuration
python -m assetutilities zip_config.yml

# With custom parameters
python -m assetutilities zip_config.yml "{'meta': {'label': 'my_scenario'}, 'analysis': {'input_directory': '../output/csv/my_data'}}"
```

### Complete Configuration Example

```yaml
meta:
  library: assetutlities
  basename: zip_utilities
  label: 03c_100yr

default:
  log_level: INFO
  config:
    overwrite:
      output: True

# Parallel processing (optional)
parallel_processing:
  enabled: true
  max_workers: 30
  timeout_per_file: 3600

# Files to be zipped
analysis:
  flag: True
  type: zip_by_stem
  by: stem
  input_directory: ../output/csv/03c_100yr
  filename:
    extension: [csv]

# Required for routing
analysis_settings:
  flag: True
  type: zip_by_stem
  by: stem

# Stem source and output
file_management:
  flag: True
  input_directory: ../03c_100yr
  output_directory: ../output/zip/03c_100yr
  filename:
    extension: [yml]
    pattern: NULL
    filters:
      contains: []
      not_contains: []
```

### Batch Processing Example

```bash
#!/bin/bash
# Process multiple scenarios

# 03c series
python -m assetutilities au_wlng_wsp_zip.yml "{'meta': {'label': '03c_100yr'}, 'analysis': {'input_directory': '../output/csv/03c_100yr'}, 'file_management': {'input_directory': '../03c_100yr', 'output_directory': '../output/zip/03c_100yr'}}"

# 04c series  
python -m assetutilities au_wlng_wsp_zip.yml "{'meta': {'label': '04c_maintenance'}, 'analysis': {'input_directory': '../output/csv/04c_maintenance'}, 'file_management': {'input_directory': '../04c_maintenance', 'output_directory': '../output/zip/04c_maintenance'}}"
```

## Configuration Reference

### Core Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analysis.flag` | Boolean | Yes | Enable analysis processing |
| `analysis.type` | String | Yes | Must be "zip_by_stem" |
| `analysis.by` | String | Yes | Must be "stem" |
| `analysis.input_directory` | String | Yes | Directory containing files to zip |
| `analysis.filename.extension` | Array | Yes | File extensions to include in ZIP |
| `analysis_settings.flag` | Boolean | Yes | Enable routing to zip utilities |
| `analysis_settings.type` | String | Yes | Must be "zip_by_stem" |
| `analysis_settings.by` | String | Yes | Must be "stem" |
| `file_management.input_directory` | String | Yes | Directory with files for stem extraction |
| `file_management.output_directory` | String | Yes | ZIP output directory |

### Parallel Processing Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `parallel_processing.enabled` | Boolean | true | Enable parallel processing |
| `parallel_processing.max_workers` | Integer | 30 | Maximum parallel workers |
| `parallel_processing.timeout_per_file` | Integer | 3600 | Timeout per file (seconds) |
| `parallel_processing.save_error_reports` | Boolean | false | Save error reports to files |
| `parallel_processing.progress_reporting` | Boolean | true | Enable progress reporting |

## Troubleshooting

### Common Issues

#### No ZIP files created
**Symptoms**: Application runs successfully but no ZIP files appear in output directory.

**Causes and Solutions**:
1. **Missing `analysis_settings` section**
   ```yaml
   # Add this section to your config
   analysis_settings:
     flag: True
     type: zip_by_stem
     by: stem
   ```

2. **Incorrect directory paths**
   - Verify `analysis.input_directory` contains the CSV files
   - Verify `file_management.input_directory` contains the stem files (YML)
   - Ensure output directory exists or can be created

3. **No matching stems**
   - Check that files in both directories share common stem patterns
   - Use debug logging: `LOG_LEVEL=DEBUG` to see file discovery

#### Files not grouping correctly
**Symptoms**: Each file creates its own ZIP instead of grouping by stem.

**Solution**: Ensure your file naming follows the stem pattern:
```
# Correct pattern (will group into stem1.zip)
stem1_data1.csv
stem1_data2.csv
stem1_config.yml

# Incorrect pattern (will create individual ZIPs)
unique_name1.csv  
unique_name2.csv
```

#### Performance issues
**Symptoms**: Processing is slow with large datasets.

**Solutions**:
1. Adjust parallel processing:
   ```yaml
   parallel_processing:
     enabled: true
     max_workers: 16  # Reduce if using too much memory
   ```

2. Process in smaller batches
3. Ensure sufficient disk space and I/O capacity

### Debug Mode

Enable debug logging to troubleshoot issues:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in Python
import os
os.environ['LOG_LEVEL'] = 'DEBUG'
```

Debug output will show:
- Files discovered in each directory
- Stem extraction results
- Grouping logic
- ZIP creation process

## Best Practices

### Configuration Management
1. **Use consistent directory structure** across all scenarios
2. **Include both `analysis` and `analysis_settings` sections** in all configs
3. **Set appropriate `max_workers`** based on system resources
4. **Use descriptive labels** matching folder names for easy identification

### File Organization
1. **Follow the three-tier directory pattern**:
   - Stem files: `../folder_name/`
   - Data files: `../output/csv/folder_name/`
   - ZIP output: `../output/zip/folder_name/`

2. **Use consistent naming conventions**:
   - Stem files: `stem_name.yml`
   - Data files: `stem_name_*.csv`
   - Output: `stem_name.zip`

### Performance Optimization
1. **Monitor system resources** when using parallel processing
2. **Batch large datasets** to avoid memory issues
3. **Use SSD storage** for better I/O performance
4. **Clean up temporary files** regularly

### Error Handling
1. **Enable error reporting** for production environments:
   ```yaml
   parallel_processing:
     save_error_reports: true
   ```

2. **Use timeouts** to prevent hanging processes:
   ```yaml
   parallel_processing:
     timeout_per_file: 3600  # 1 hour max per file
   ```

3. **Validate configurations** before running large batches
4. **Monitor log files** for warnings and errors

---

For additional support or feature requests, please refer to the main AssetUtilities documentation or submit an issue to the project repository.