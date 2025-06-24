import os
import sys
import io
import pandas as pd

from typing import List, Dict, Any
from zipfile import ZipExtFile
from loguru import logger
from assetutilities.modules.csv_utilities.csv_utilities import CSVUtilities

csv_utilities = CSVUtilities()

class CSVUtilitiesRouter:

    def router(self,cfg):
        csv_utilities.read_zip_file_with_latin1()
    