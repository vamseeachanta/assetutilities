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
import pandas as pd
from data_manager.argumentParseFunction import *
from data_manager.dataFrametoDatabase import *
from data_manager.SQLtoDataFrame import *

configData = argumentParseFunction()


connection = MySQLdb.connect(
    host=configData.MySQLServerName[0],
    db=configData.MySQLDatabaseName[0],
    user=configData.MySQLUserName[0],
    passwd=configData.MySQLPassword[0],
)
cursor = connection.cursor()
print("db connection successful using MySQLdb")


# Define a table, table columns and SQL codes (for read and write)
tableName1 = "projects"
projects_header = ["ProjectName", "Operator", "Location", "ProjectType", "Data"]
projectDF = pd.DataFrame(columns=projects_header)

projectsSQL = "SELECT * FROM " + tableName1
commitSQL = (
    "INSERT INTO "
    + tableName1
    + "(ProjectName, Operator, Location, ProjectType, Data) VALUES"
)

# Read and display data before insert
df = SQLtoDataFrame(connection, projectsSQL)
print(df)

# define sample data and insert into database
projectDF.loc[len(projectDF)] = [
    "ThunderHorse",
    "BP",
    "Gulf of Mexico",
    "Semi",
    "{Latitude: xx, logitude: xx,}",
]
dataFrametoDatabase(connection, cursor, commitSQL, projectDF)

# Read and display data after insert
df = SQLtoDataFrame(connection, projectsSQL)
print(df)
