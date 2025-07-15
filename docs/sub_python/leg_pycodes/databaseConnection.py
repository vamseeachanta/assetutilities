#!/usr/bin/env python3

"""
Author: Vamsee Achanta
Date Updated: 2017-11-16
Objective: database connection
Outputs: Connection and Cursor (to read data)
Future Improvements:
- Make databaseConnection() into an argument function for more database types.
- Pass more database connection parameters as function arguments
"""


def databaseConnection(serverType, serverName, databaseName, userName, userPassword):
    if serverType == "MSSQL":
        import pymssql

        conn = pymssql.connect(
            server=serverName,
            user=userName,
            password=userPassword,
            database=databaseName,
        )

    elif serverType == "Oracle":
        import cx_Oracle

        conn = cx_Oracle.connect(userName, userPassword, serverName)

    cursor = conn.cursor()
    return (conn, cursor)
