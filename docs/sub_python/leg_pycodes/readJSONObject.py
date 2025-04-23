#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Author: Vamsee Achanta
Date Created: 2017-10-31
Objective: To read generic JSON dataObject
Usage : ReadJsonData (filename/cursorData, item, [itemFamily])
Outputs: Vector of data
Future Improvements: 
 - Test for other JSON formats
'''
def readJSONObject(objectName,itemName,itemFamily=""):
    import json
    
    if ".json" in objectName:
        with open(objectName) as data_file:  
            data = json.load(data_file)
    else:
        data = objectName
        
    output = []
    if itemFamily == "":
        for i in range(0, len(data)):
            output.append(data[i][itemName])
        return output

    else:
        # Code needs to be tested and updated with json objects with itemFamily
        for i in data[itemFamily]:
            for k,v in i.items():
                if k==itemName:
                    output.append(v)
        return output
