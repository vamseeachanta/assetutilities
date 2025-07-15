## Import the json module and os module
import json
import os


## function for reading JSON file
def ReadJsonFile(filename):
    ## creating an empty list
    data_list = []
    ## open JSON file and read the data in it as 'data_file'
    with open(filename) as data_file:
        ## extracting the data from file using json.load()
        data = json.load(data_file)
        print(data)
        for i in data:
            ## appending the extracted data into list[]
            data_list.append(i)
        print(data_list)


## providing the path for the JSON files
path_to_json = "C:/Users/Desktop/project/"  # Add your files path here change '\' to '/'
## Writing condition to check the file is JSON by endswith('.json')
json_files = [
    pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith(".json")
]
print(json_files)

for file in json_files:
    ## JSON files stored in json_files list and passing them as arguments to Function ReadJsonFile()
    ReadJsonFile(file)
