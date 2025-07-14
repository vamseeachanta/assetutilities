"""
Author: Vamsee Achanta
Date Updated: 2018-04-10
Objective: mySQL connection (using python)
Outputs: connection & cursor for further operations
Running Program:
python createTableSQLCode.py --SQLType "MS SQL" --tableName "[programTestLog, New]" --tableColumns "{'columnName' : 'ID', 'columnType' : 'Identity', 'columnAttribues': 'PRIMARY KEY'}, {'columnName' : 'ProgramName',  'columnType' : 'CHAR', 'columnAttribues': 50}, {'columnName' : 'FileObjects',  'columnType' : 'TEXT', 'columnAttribues': None}" --log DEBUG

"""

import munch
from data_manager.argumentParseFunction import *
from data_manager.setLogging import *

# Get configuration data
configData = argumentParseFunction()
# Set logging settings
setLogging(configData.log[0])

# Print key quantities for information
logging.info(
    "The logging mode is " + configData.log[0]
)  # will print a message to the console
logging.info(configData.tableColumns[0])
logging.info(configData.SQLType[0])

tableColumnData = munch.munchify(configData.tableColumns[0])

print(tableColumnData)

# for i in range(0, len(tableColumnData)):
