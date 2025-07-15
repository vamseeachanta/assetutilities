from cassandra.cluster import Cluster

##from saveData import LoadData

cluster = Cluster()
session = cluster.connect()


def CreateTable(keyspacename, tablename):
    session.execute(
        "CREATE KEYSPACE "
        + str(keyspacename)
        + " with replication={'class': 'SimpleStrategy', 'replication_factor': '3'}"
    )
    session.execute("USE " + str(keyspacename))
    session.execute(
        "CREATE TABLE "
        + str(tablename)
        + "(user_id int,name text,numb int,PRIMARY KEY(user_id))"
    )
    session.execute(
        "INSERT INTO "
        + str(keyspacename)
        + "."
        + str(tablename)
        + " (user_id ,name ,numb ) VALUES (1,'John',000123456)"
    )
    result = session.execute("SELECT * from " + str(tablename) + ";")
    for x in result:
        print(x)


CreateTable(keyspacename="exampleKeyspace", tablename="y")
##
##LoadData(x= 0,y= 'Sam',z = 964292)
##LoadData(x= 1,y = 'Smith',z = 456)
##LoadData(x= 2,y = 'Alex',z = 789456)
