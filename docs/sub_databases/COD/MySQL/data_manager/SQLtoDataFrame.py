#!/usr/bin/env python3

"""
Author: Vamsee Achanta
Date Updated: 2017-11-25
Objective: To pass a database query and obtain data as Pandas Dataframe
Outputs: Pandas DataFrame
"""

import pandas.io.sql as psql


def SQLtoDataFrame(connection, SQLScript):
    df = psql.read_sql(SQLScript, connection)
    return df
