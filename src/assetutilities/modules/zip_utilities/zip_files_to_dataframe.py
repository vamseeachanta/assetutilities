import pandas as pd
import zipfile
import os
from typing import Dict, List, Optional, Union

from io import BytesIO

class ZipFilestoDf:

    def __init__(self):
        pass

    def router(self,cfg):
        self.zip_to_dataframes(cfg)
        return cfg
    
    def zip_to_dataframes(self,cfg) ->  Union[Dict[str, pd.DataFrame], pd.DataFrame]:
        
        """
        Extracts CSV or TXT files from a ZIP archive and loads them and returns Pandas DataFrames.
        
        Returns:
            Union[Dict[str, pd.DataFrame], pd.DataFrame]:
            - A single DataFrame if there's only one CSV/TXT file in zip.
            - A dictionary where keys are filenames and values are Pandas DataFrames if multiple files exist.
        """
        
        folder_path = cfg['zip_utilities']['folder_path']
        column_names = None # Default to None, can be set in the configuration if needed

        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"The folder path '{folder_path}' is not valid to load zip files.")

        for file_name in os.listdir(folder_path):
            if file_name.endswith(".zip"):
                zip_filepath = os.path.join(folder_path, file_name)
                # Load the ZIP file into memory
                with open(zip_filepath, "rb") as f:
                    zip_bytes = f.read()
        zip_file = zip_bytes

         # Ensure the input is a file-like object
        if isinstance(zip_file, bytes):
            zip_file = BytesIO(zip_file)
        
        with zipfile.ZipFile(zip_file, 'r') as zf:
            file_list = zf.namelist()
            
            # list CSV or TXT files
            csv_or_txt_files = [f for f in file_list if f.lower().endswith(('.csv', '.txt'))]
            if not csv_or_txt_files:
                raise ValueError("No CSV or TXT files found in the ZIP archive.")
            
            dataframes = {}
            delimiter = ','
            for file_to_read in csv_or_txt_files:
                with zf.open(file_to_read) as txtcsvf:
                    df = pd.read_csv(txtcsvf, sep=delimiter)
                    
                    # If column names are provided and the df has no header(columns are defaulted to integers), set the column names
                    if column_names is not None and all(isinstance(col, int) for col in df.columns): 
                        df.columns = column_names
                    
                    print(f"Loaded file: {file_to_read}")
                    dataframes[file_to_read] = df
            
            # If only one file, return the DataFrame instead of a dictionary
            if len(dataframes) == 1:
                return list(dataframes.values())[0]
            
            return dataframes