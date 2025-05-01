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
    
    def zip_file_to_dataframe(self, cfg) ->  Union[Dict[str, pd.DataFrame], pd.DataFrame]:

        """
        Extracts files from a ZIP file/archive and returns Pandas DataFrame(s) arrayarray.

        Returns:
            Union[Dict[str, pd.DataFrame], pd.DataFrame]:
            - A single DataFrame if there's only one CSV/TXT file in zip.
            - A dictionary where keys are filenames and values are Pandas DataFrames if multiple files exist.
        """

        column_names = cfg['zip_utilities']['column_names']
        zip_file_name_with_path = cfg['zip_utilities']['file_name']

        with open(zip_file_name_with_path, "rb") as f:
            zip_bytes = f.read()

        zip_file = zip_bytes

         # Ensure the input is a file-like object
        if isinstance(zip_file, bytes):
            zip_file = BytesIO(zip_file)

        with zipfile.ZipFile(zip_file, 'r') as zf:
            file_list = zf.namelist()

            # check if file_list is empty
            if not file_list:
                raise ValueError(f"The ZIP file '{zip_file_name_with_path}' is empty.")

            dataframe_dict = {}
            delimiter = ','
            for file_to_read in file_list:
                with zf.open(file_to_read) as file:
                    try:
                        df = pd.read_csv(file, sep=delimiter)
                    except Exception as e:
                        try:
                            df = pd.read_csv(file, sep=delimiter, encoding='unicode_escape')
                        except Exception as e:
                            logger.error(f"Error reading file '{file_to_read}': {e}")
                            continue

                    # If column names are provided and the df has no header set the column names
                    if column_names: 
                        df.columns = column_names

                    file_basename = os.path.basename(file_to_read)
                    file_name_without_extension, extension = os.path.splitext(file_basename)
                    dataframe_dict[file_name_without_extension] = df

        return dataframe_dict

