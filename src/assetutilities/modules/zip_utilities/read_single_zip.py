import pandas as pd
import zipfile
import os
from typing import Dict, List, Optional

class ReadSingleZip:

    def __init__(self):
        pass

    def router(self,cfg):
        
        if cfg['zip']['mode'] == 'single':
            dfs = self.extract_zip_to_dataframes(cfg['zip_filepath'], cfg['column_names'])
        return cfg
    
    def extract_zip_to_dataframes(self,zip_filepath: str, column_names: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Extracts CSV or TXT files from a ZIP archive and loads them into separate Pandas DataFrames.
        
        Parameters:
            zip_filepath (str): Path to the ZIP file.
            column_names (Optional[List[str]]): Column names to use if the file has no header. Defaults to None.
        
        Returns:
            Dict[str, pd.DataFrame]: A dictionary where keys are filenames and values are Pandas DataFrames.
        """
        delimiter = ','
        
        with zipfile.ZipFile(zip_filepath, 'r') as zf:
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
            
            return dataframes

