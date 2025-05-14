import pandas as pd
import zipfile
import os
from typing import Dict, List, Optional, Union
from loguru import logger

from io import BytesIO

class ZipFilestoDf:

    def __init__(self):
        pass

    def router(self,cfg):
        pass
    
    def zip_file_to_dataframe(self, cfg) -> Dict[str, pd.DataFrame]:

        """ Extracts files from a ZIP file/archive and returns Pandas DataFrame(s) as dictionary."""

        column_names = cfg['zip_utilities']['column_names']
        zip_file_name_with_path = cfg['zip_utilities']['file_name']
        rows = 50000 # to limit file size 

        with open(zip_file_name_with_path, "rb") as f:
            zip_bytes = f.read()

        zip_file = zip_bytes

        if isinstance(zip_file, bytes):
            zip_file = BytesIO(zip_file)

        with zipfile.ZipFile(zip_file, 'r') as zf:
            files_in_zip = zf.namelist()
            file_list = [name for name in files_in_zip if not name.endswith('/')]

            # check if file_list is empty
            if not file_list:
                raise ValueError(f"The ZIP file '{zip_file_name_with_path}' is empty.")

            dataframe_dict = {}
            delimiter = ','
            dataframe_dict = self.parse_zip_files(column_names, rows, zf, file_list, dataframe_dict, delimiter)

        return dataframe_dict

    def parse_zip_files(self, column_names, rows, zf, file_list, dataframe_dict, delimiter):
        
        for file_to_read in file_list:
            with zf.open(file_to_read) as file:
                try:
                    df = pd.read_csv(file, sep=delimiter, on_bad_lines='warn',low_memory=False,nrows=rows)
                except Exception as e:
                    try:
                        df = pd.read_csv(file, sep=delimiter, encoding='latin-1', on_bad_lines='warn',low_memory=False,nrows=rows)
                    except Exception as e:
                        logger.error(f"Error reading file '{file_to_read}': {e}")
                        continue
  
                # If column names are provided and the df has no header set the column names
                if column_names: 
                    df.columns = column_names

                file_basename = os.path.basename(file_to_read)
                file_name_without_extension, extension = os.path.splitext(file_basename)
                dataframe_dict[file_name_without_extension] = df

