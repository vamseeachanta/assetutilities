## Zip utilities

### Overview
This module provides utilities for working with zip files, including creating, extracting, and listing contents of zip files. It is designed to be used in conjunction with other modules that handle file operations and data processing.

## Utilizing zip instead of csv files 

Aim : To use zip files instead of csv files for data storage and transfer. This approach aims to read zip files directly into pandas dataframes, eliminating the need for intermediate csv files.

Beneifits: 
- Zip files are compressed, which can save storage space and reduce transfer times.
- Zip files can contain multiple files, allowing for better organization and packaging of related data.
- No csv files are created, which can reduce the risk of data corruption or loss during file operations.

### Update Configuration

To use this module , the configuration needs to be updated to include the following settings:

```python
cfg['zip_utilities'] = {
            'input_directory': folder_path,
            'column_names': column_names # only if your df has no header
        }
```

custom script for zip files to pandas dataframe:
src\assetutilities\modules\zip_utilities\zip_files_to_dataframe.py
