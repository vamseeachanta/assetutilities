import csv
from pprint import pprint

from cassandra.cluster import Cluster
from pymongo import MongoClient


class ExportCSV:
    def Cassandra(keyspacename, tablename, file):
        f = open(file)
        csv_f = csv.reader(f)
        cluster = Cluster()
        session = cluster.connect()
        session.execute(
            "CREATE KEYSPACE "
            + str(keyspacename)
            + " with replication={'class': 'SimpleStrategy', 'replication_factor': '3'}"
        )
        session.execute("USE " + str(keyspacename))
        session.execute(
            "CREATE TABLE "
            + str(tablename)
            + "(column1 text,column2 int,column3 int,column4 float,column5 float,PRIMARY KEY(column3))"
        )
        for row in csv_f:
            session.execute(
                "INSERT INTO datatable(column1,column2,column3,column4,column5) VALUES('{}',{},{},{},{})".formate(
                    row[0], row[1], row[2], row[3], row[4]
                )
            )
        result = session.execute("SELECT * from " + str(tablename))
        for x in result:
            print(x)
        cluster.shutdown()

    def MongoDB(db_name, coll_name, file):
        f = open(file)
        csv_f = csv.reader(f)
        noofrow = 0
        for row in csv_f:
            noofrow = 1 + noofrow
            collen = len(row[0]) + 1
        print(collen)
        print(noofrow)
        connection = MongoClient("localhost", 27017)
        print(db_name, coll_name)
        data = connection[str(db_name)][str(coll_name)]
        ##        for row in csv_f:
        ##             Listdata = data.insert(
        ##                 {"column1":row[0],"column2":row[1],"column3":row[2],"column4":row[3],"column5":row[4]})
        Listdata = data.find()
        for doc in Listdata:
            pprint(doc)
        connection.close()


ExportCSV.MongoDB("sampleDB", "exportedData", "environmentLoading.csv")
ExportCSV.Cassandra("sampleDB", "exportedData", "environmentLoading.csv")
