import csv

f = open("environmentLoading.csv")
csv_f = csv.reader(f)

from cassandar.cluster import Cluster

cluster = Cluster()

session = cluster.connect()

session.execute(
    "CREATE KEYSPACE evironmentLoading with replication={'class': 'SimpleStrategy', 'replication_factor': '3'}"
)

session.execute("USE evironmentLoading")

session.execute(
    "CREATE TABLE datatable(column1 text,column2 int,column3 int,column4 float,column5 float,PRIMARY KEY(column3))"
)

for row in csv_f:
    print(row)
    session.execute(
        "INSERT INTO datatable(column1,column2,column3,column4,column5) VALUES('{}',{},{},{},{})".formate(
            row[0], row[1], row[2], row[3], row[4]
        )
    )

result = session.execute("SELECT * from datatable")
datatable
for x in result:
    print(x)

cluster.shutdown()
