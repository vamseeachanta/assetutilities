import os
import sys
import io
import pandas as pd

from typing import List, Dict, Any
from zipfile import ZipExtFile
from loguru import logger

class CSVUtilities:

    def router(self,cfg):
        pass

    def read_zip_file_with_latin1(self, file: ZipExtFile,
                           delimiter: str = ',', 
                           nrows: int = None) -> pd.DataFrame:
        """
        Reads a file from a ZIP archive with Latin-1 encoding.
        """
        try:
            text_file = io.TextIOWrapper(file)
            df = pd.read_csv(text_file, sep=delimiter, on_bad_lines='warn',
                            low_memory=False, nrows=nrows)
        except UnicodeDecodeError:
            file.seek(0)
            text_file = io.TextIOWrapper(file, encoding='latin-1')
            df = pd.read_csv(text_file, sep=delimiter, on_bad_lines='warn',
                            low_memory=False, nrows=nrows)
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise 
        return df
    
    
    #TODO: Add more methods as needed for CSV utilities