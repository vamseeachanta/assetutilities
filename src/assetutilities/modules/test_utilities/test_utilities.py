# Standard library imports

# Standard library imports
import os

# Third party imports
import pandas as pd


class TestUtilities:
    def __init__(self):
        pass

    def get_valid_pytest_output_file(
        self, parent_directory, pytest_output_file: str
    ) -> str:
        if pytest_output_file is not None and not os.path.isfile(pytest_output_file):
            pytest_output_file = os.path.join(parent_directory, pytest_output_file)
            pytest_output_file = os.path.abspath(pytest_output_file)
        if not os.path.isfile(pytest_output_file):
            raise Exception("Not valid file. Please check the file path.")
        return pytest_output_file

    def check_csv_files_match(self, file1: str, file2: str) -> bool:
        df_file1 = pd.read_csv(file1)
        df_file2 = pd.read_csv(file2)

        file_match_result = df_file1.equals(df_file2)

        return file_match_result
