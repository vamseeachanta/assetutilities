import os
import sys
import io
import pandas as pd
import zipfile

from typing import List, Dict, Any
from zipfile import ZipExtFile
from loguru import logger

class CSVUtilities:

    def router(self,cfg):
        pass

    def read_zip_file_with_latin1(self,cfg) -> pd.DataFrame:
        """
        Reads a file from a ZIP archive with Latin-1 encoding.
        """
        
        cfg_Zipext_file = cfg['csv_utilities']['file']
        delimiter = cfg['csv_utilities']['delimiter'] if 'delimiter' in cfg['csv_utilities'] else ','
        nrows = cfg['csv_utilities']['nrows'] if 'nrows' in cfg['csv_utilities'] else None
        try:
            text_file = io.TextIOWrapper(cfg_Zipext_file)
            df = pd.read_csv(text_file, sep=delimiter, on_bad_lines='warn',
                            low_memory=False, nrows=nrows)
        except UnicodeDecodeError:
            cfg_Zipext_file.seek(0)
            text_file = io.TextIOWrapper(cfg_Zipext_file, encoding='latin-1')
            df = pd.read_csv(text_file, sep=delimiter, on_bad_lines='warn',
                            low_memory=False, nrows=nrows)
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise 
        return df
    
    
    #TODO: Add more methods as needed for CSV utilities