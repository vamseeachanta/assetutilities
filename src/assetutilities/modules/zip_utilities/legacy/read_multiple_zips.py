import pandas as pd
import zipfile
import os
from typing import Dict, List, Optional

class ReadMultipleZips:

    def __init__(self):
        pass

    def router(self,cfg):

        if cfg['zip']['files'] == 'multiple':
            dfs = self.multiple_zips_to_dataframes(cfg['zip_folderpath'], cfg['column_names'])
        return cfg

    def multiple_zips_to_dataframes(folder_path: str, column_names: Optional[List[str]] = None) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Extracts CSV or TXT files from multiple ZIP archives in a folder and loads them into separate Pandas DataFrames.
        
        Parameters:
            folder_path (str): Path to the folder containing ZIP files.
            column_names (Optional[List[str]]): Column names to use if the file has no header. Defaults to None.
        
        Returns:
            Dict[str, Dict[str, pd.DataFrame]]: A dictionary where keys are ZIP filenames and values are dictionaries 
            mapping CSV/TXT filenames to Pandas DataFrames.
        """
        delimiter = ','
        zip_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.zip')]
        
        if not zip_files:
            raise ValueError("No ZIP files found in the specified folder.")
        
        all_dataframes = {}
        
        for zip_filename in zip_files:
            zip_filepath = os.path.join(folder_path, zip_filename)
            
            with zipfile.ZipFile(zip_filepath, 'r') as zf:
                file_list = zf.namelist()
                
                # Identify CSV or TXT files
                csv_or_txt_files = [f for f in file_list if f.lower().endswith(('.csv', '.txt'))]
                if not csv_or_txt_files:
                    print(f"No CSV or TXT files found in {zip_filename}, skipping...")
                    continue
                
                dataframes = {}
                for file_to_read in csv_or_txt_files:
                    with zf.open(file_to_read) as txtf:
                        df = pd.read_csv(txtf, sep=delimiter)
                        
                        # If column names are provided and the file has no header, set column names
                        if column_names and df.columns[0] == df.index.name:
                            df.columns = column_names
                        
                        print(f"Loaded file: {file_to_read} from {zip_filename}")
                        dataframes[file_to_read] = df
                
                all_dataframes[zip_filename] = dataframes
        
        return all_dataframes
