from cassandra.cluster import Cluster

cluster = Cluster()
session = cluster.connect()
session.execute("CREATE KEYSPACE Sample_keyspace53 with replication={'class': 'SimpleStrategy', 'replication_factor': '3'}")
## Created a keyspace named"sample_keyspace"
session.execute("USE sample_keyspace53")
session.execute("CREATE TABLE sample_table(user_id int,name text,numb int,PRIMARY KEY(user_id))")
## Created a tablename as "sample_table"
session.execute("INSERT INTO sample_table (user_id ,name ,numb ) VALUES (1,'John',000123456)")
result = session.execute("SELECT * from sample_table")
for x in result:
    print(x)

cluster.shutdown()
