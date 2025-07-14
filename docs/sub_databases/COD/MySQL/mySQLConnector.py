"""
Author: Vamsee Achanta
Date Updated: 2018-04-10
Objective: mySQL connection (using python)
Outputs: connection & cursor for further operations
Running Program:
python mySQLConnector.py --MySQLServerName="73.166.60.103" --MySQLDatabaseName="krishna-d" --MySQLUserName="AceEngineer" --MySQLPassword="Ace@DataWare!2020"
python mySQLConnector.py --MySQLServerName="localhost" --MySQLDatabaseName="krishna-d" --MySQLUserName="AceEngineer" --MySQLPassword="Ace@DataWare!2020"
"""

import MySQLdb
from data_manager.argumentParseFunction import *

configData = argumentParseFunction()


db = MySQLdb.connect(
    host=configData.MySQLServerName[0],
    db=configData.MySQLDatabaseName[0],
    user=configData.MySQLUserName[0],
    passwd=configData.MySQLPassword[0],
)
cur = db.cursor()
print("db connection successful using MySQLdb")
