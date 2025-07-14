#!/usr/bin/env python3

"""
Author: Vamsee Achanta
Date Updated: 2017-11-21
Objective: To pass a database query and obtain data as Pandas Dataframe
Outputs: Pandas DataFrame
"""


def dataFrametoDatabase(conn, cursor, commitSQL, df):
    records = [str(tuple(x)) for x in df.values]

    for batch in chunker(records, 1000):
        rows = ",".join(batch)
        insert_rows = commitSQL + rows
        cursor.execute(insert_rows)
        conn.commit()


def chunker(seq, size):
    return (seq[pos : pos + size] for pos in range(0, len(seq), size))
