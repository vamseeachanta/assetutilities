import pandas as pd
import zipfile
import os
from typing import Dict, List, Optional, Union

from io import BytesIO

class ReadZiptoDf:

    def __init__(self):
        pass
    
    def zip_to_dataframes(self,zip_file: Union[BytesIO, bytes], column_names: Optional[List[str]] = None) ->  Union[Dict[str, pd.DataFrame], pd.DataFrame]:
        
        """
        Extracts CSV or TXT files from a ZIP archive and loads them into separate Pandas DataFrames.
        
        Parameters:
            zip_filepath (str): Path to the ZIP file.
            column_names (Optional[List[str]]): Column names to use if the file has no header. Defaults to None.
        
        Returns:
            Union[Dict[str, pd.DataFrame], pd.DataFrame]:
            - A single DataFrame if there's only one CSV/TXT file.
            - A dictionary where keys are filenames and values are Pandas DataFrames if multiple files exist.
        """
        delimiter = ','
        zip_file = zip_file
        column_names = column_names

         # Ensure the input is a file-like object
        if isinstance(zip_file, bytes):
            zip_file = BytesIO(zip_file)
        
        with zipfile.ZipFile(zip_file, 'r') as zf:
            file_list = zf.namelist()
            
            # Identify CSV or TXT files
            csv_or_txt_files = [f for f in file_list if f.lower().endswith(('.csv', '.txt'))]
            if not csv_or_txt_files:
                raise ValueError("No CSV or TXT files found in the ZIP archive.")
            
            dataframes = {}
            for file_to_read in csv_or_txt_files:
                with zf.open(file_to_read) as txtcsvf:
                    df = pd.read_csv(txtcsvf, sep=delimiter)
                    
                    # If column names are provided and the file has no header, set column names
                    if column_names is not None:
                        df.columns = column_names
                    
                    print(f"Loaded file: {file_to_read}")
                    dataframes[file_to_read] = df
            
            # If only one file, return the DataFrame directly
            if len(dataframes) == 1:
                return list(dataframes.values())[0]
            
            return dataframes