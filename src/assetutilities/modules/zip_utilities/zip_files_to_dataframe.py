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
        if cfg['zip_utilities']['technique'] == 'zip_files_to_df':
            cfg = self.zip_to_dataframes(cfg)
        return cfg
    
    def zip_to_dataframes(self,cfg) ->  Union[Dict[str, pd.DataFrame], pd.DataFrame]:
        
        """
        Extracts files from a ZIP archive , loads them and returns Pandas DataFrame.
        
        Returns:
            Union[Dict[str, pd.DataFrame], pd.DataFrame]:
            - A single DataFrame if there's only one CSV/TXT file in zip.
            - A dictionary where keys are filenames and values are Pandas DataFrames if multiple files exist.
        """
        
        zip_directory = cfg['zip_utilities']['input_directory'] 
        column_names = cfg['zip_utilities']['column_names'] # customize both according to your configuration

        if not os.path.exists(zip_directory):
            raise FileNotFoundError(f"The specified folder path '{zip_directory}' does not exist.")

        for file_name in os.listdir(zip_directory):
            if file_name.endswith(".zip"):
                zip_filepath = os.path.join(zip_directory, file_name)
                # Load the ZIP file into memory
                with open(zip_filepath, "rb") as f:
                    zip_bytes = f.read()

        zip_file = zip_bytes

         # Ensure the input is a file-like object
        if isinstance(zip_file, bytes):
            zip_file = BytesIO(zip_file)
        
        with zipfile.ZipFile(zip_file, 'r') as zf:
            file_list = zf.namelist()
            
            # check if file_list is empty
            if not file_list:
                raise ValueError(f"The ZIP file '{zip_filepath}' is empty.")
            
            dataframes = {}
            delimiter = ','
            for file_to_read in file_list:
                df = pd.DataFrame()
                with zf.open(file_to_read) as file:
                    try:
                        df = pd.read_csv(file, sep=delimiter)
                    except Exception as e:
                        try:
                            df = pd.read_csv(file, sep=delimiter, encoding='unicode_escape')
                        except Exception as e:
                            logger.error(f"Error reading file '{file_to_read}': {e}")

                    # If column names are provided and the df has no header set the column names
                    if len(df) > 0 and column_names:
                        df.columns = column_names
                    #logger.debug(f"Loaded file: {file_to_read}")
                    file_basename = os.path.basename(file_to_read)
                    file_name_without_extension, extension = os.path.splitext(file_basename)
                    dataframes[file_name_without_extension] = df

            # If only one file, return the DataFrame instead of a dictionary
            if len(dataframes) == 1:
                return list(dataframes.values())[0]
            else:
                return dataframes
            
    def zip_to_dataframe_by_filename(self, cfg) ->  Union[Dict[str, pd.DataFrame], pd.DataFrame]:
        
        """
        Extracts files from a ZIP archive , loads them and returns Pandas DataFrame.
        
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
                raise ValueError(f"The ZIP file '{zip_filepath}' is empty.")
            
            dataframes = {}
            delimiter = ','
            for file_to_read in file_list:
                with zf.open(file_to_read) as file:
                    df = pd.read_csv(file, sep=delimiter)
                    
                    # If column names are provided and the df has no header set the column names
                    if column_names: 
                        df.columns = column_names
                    
                    #logger.debug(f"Loaded file: {file_to_read}")
                    file_name = os.path.splitext(file_to_read)[0]
                    dataframes[file_name] = df
            
            # If only one file, return the DataFrame instead of a dictionary
            if len(dataframes) == 1:
                return list(dataframes.values())[0]
            else:
                return dataframes