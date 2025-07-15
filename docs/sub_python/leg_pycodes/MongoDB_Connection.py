from pymongo import MongoClient

# connect to Database
connection = MongoClient("localhost", 27017)
db = connection.mydb

# handle to friends Collection
data = db.friends

##inserting multiple documents

friendList = db.friends.insert(
    [
        {"name": "Jane", "age": "22"},
        {"name": "Alex", "age": "23"},
        {"name": "Jhoana", "age": "24"},
        {"name": "Walter", "age": "25"},
    ]
)

friendsList = data.find()

for item in friendsList:
    print("Name: " + item["name"] + ", Age: " + str(item["age"]))

connection.close()  ##End the MongoDB connections
