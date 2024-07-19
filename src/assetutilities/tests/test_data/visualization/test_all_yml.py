# read all yml files in the current directory
# Loop through each yml file and run the below command
  # Hint1: python subprocess;  (Easier route). 
  # Hint2: subprocess separate command prompt. You have to open a minconda prompt and ensure same python enviornment is used to run each yml file
# If it ran, get success or failure. If one yml file fails.. then fail the test else the test passes
    # save a csv with all success and failures.

import os
import subprocess
import pandas as pd

def run_yaml_files(directory):
    
    filenames = []
    statuses = []

    for filename in os.listdir(directory):
        if filename.endswith('.yml') or filename.endswith('.yaml'):
            file_path = os.path.join(directory, filename)
            try:
                result = subprocess.run(['python', '-m', 'assetutilities', file_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(result.stdout.decode())  
                filenames.append(filename)
                statuses.append('Success')
            except subprocess.CalledProcessError as e:
                print(e.stderr.decode())  
                filenames.append(filename)
                statuses.append('Failed')

    df = pd.DataFrame({'Filename': filenames, 'Status': statuses})
    output_csv = os.path.join(directory, 'file_status.csv')
    df.to_csv(output_csv, index=False)

directory = r'src\assetutilities\tests\test_data\visualization'
run_yaml_files(directory)

