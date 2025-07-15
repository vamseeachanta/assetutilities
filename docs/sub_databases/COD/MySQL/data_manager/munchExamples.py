#!/usr/bin/env python3

"""
Author: Vamsee Achanta
Date Updated: 2018-04-23
Objective: To test munch module with standard examples
Outputs: Output format from munch will determine suitability of usage of munch
"""

import munch

data_json1 = [
    {"columnName": "ID", "columnType": "Identity", "columnAttribues": "PRIMARY KEY"},
    {"columnName": "ProgramName", "columnType": "CHAR", "columnAttribues": 50},
    {"columnName": "FileObjects", "columnType": "TEXT", "columnAttribues": None},
]


tableColumns = munch.munchify(data_json1)

plateGData1 = {
    "PlateLength": 2.69,
    "PlateLength_unit": "m",
    "PlateBreadth": 0.70,
    "PlateBreadth_unit": "m",
    "PlateThickness": 0.014,
    "PlateThickness_unit": "m",
    "AverageWaterDepth": 40,
    "AverageWaterDepth_unit": "m",
    "YieldStrength": 34,
    "YieldStrength_unit": "ksi",
    "PoissionsRatio": 0.30,
    "YoungsModulus": 30450,
    "YoungsModulus_unit": "ksi",
}

plateGData = munch.munchify(plateGData1)


print(len(tableColumns))
print(tableColumns[2].columnAttribues)
