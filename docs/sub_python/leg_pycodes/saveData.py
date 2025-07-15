from cassandra.cluster import Cluster

##from createCassandraKeyspaceTable import CreateTable
## createCassandraKeyspaceTable.py is python file and CreateTable() is a funtion where we imported

cluster = Cluster()
session = cluster.connect()


def LoadData(x, y, z):
    ##    CreateTable(keyspacename=x,tablename=y) #Inherited CreateTable funtion propeties from createCassandraKeyspaceTable.py file
    session.execute(
        "INSERT INTO x.y (user_id ,name, numb) VALUES ("
        + str(x)
        + ","
        + str(y)
        + ","
        + str(z)
        + ")"
    )


##LoadData(x = "keyspace0",y = "sample_table")
LoadData(x=0, y="Sam", z=964292)
LoadData(x=1, y="Smith", z=456)
LoadData(x=2, y="Alex", z=789456)
