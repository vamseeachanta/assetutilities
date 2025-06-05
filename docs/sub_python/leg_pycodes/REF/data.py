import json
import os
import pymssql
import cx_Oracle
import pandas
import pandas.io.sql as psql
from enum import Enum


class ServerType(Enum):
    MSSQL = 1
    ORACLE = 2
    CSV = 3


class CipherData:
    __connection = None
    serverType = None
    serverName = None
    databaseName = None
    userName = None
    userPassword = None
    chunksize = 1000

    def __init__(self, serverType, serverName=None, databaseName=None, userName=None, userPassword=None, chunksize=1000):
        if isinstance(serverType, ServerType):
            self.serverType = serverType
        elif isinstance(serverType, str):
            if serverType.upper() == "MSSQL":
                self.serverType = ServerType.MSSQL
            elif serverType.upper() == "ORACLE":
                self.serverType = ServerType.ORACLE
            elif serverType.upper() == "CSV":
                self.serverType = ServerType.CSV
        self.serverName = serverName
        self.databaseName = databaseName
        self.userName = userName
        self.userPassword = userPassword
        self.chunksize = chunksize

    @staticmethod
    def byName(name):
        # load parameters using name
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        with open(os.path.join(__location__, 'servers.json'), 'r') as f:
            servers = json.load(f)
            server = servers[name]
            return CipherData(server["SQLType"], server["DBServerName"], server["DBName"], server["UserName"], server["Password"])

    @property
    def connection(self):
        if self.__connection is None:
            if self.serverType is ServerType.MSSQL:
                self.__connection = pymssql.connect(server=self.serverName,
                                                    user=self.userName,
                                                    password=self.userPassword,
                                                    database=self.databaseName)
            elif self.serverType is ServerType.ORACLE:
                self.__connection = cx_Oracle.connect(self.userName,
                                                      self.userPassword,
                                                      self.serverName)
            else:
                self.__connection = None
        return self.__connection

    @staticmethod
    def fromCsv(path):
        csv = CipherData(ServerType.CSV)
        return csv.load(path)

    @staticmethod
    def fromDb(dbname, sql):
        db = CipherData.byName(dbname)
        return db.load(sql)

    @staticmethod
    def toDb(dbname, dataframe, tablename):
        db = CipherData.byName(dbname)
        db.save(dataframe, tablename)

    def load(self, sql_or_csvpath):
        df = None
        if self.serverType is ServerType.MSSQL or self.serverType is ServerType.ORACLE:
            df = psql.read_sql_query(sql_or_csvpath, self.connection)
        elif self.serverType is ServerType.CSV:
            df = pandas.read_csv(sql_or_csvpath)
        return df

    def save(self, dataframe, tablename):
        commitSQL = "insert into " + tablename + " VALUES "

        connection = self.connection
        cursor = connection.cursor()
        cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'")

        def chunker(seq, size):
            return (seq[pos:pos + size] for pos in range(0, len(seq), size))

        records = [str(tuple(row)) for row in dataframe.values]

        for batch in chunker(records, 1000):
            rows = ','.join(batch)
            insert_rows = commitSQL + rows
            cursor.execute(insert_rows)
            connection.commit()
