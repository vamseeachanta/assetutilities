import pymongo
from pymongo import MongoClient
from pprint import pprint
import csv
f = open('environmentLoading.csv')
csv_f = csv.reader(f)

#connect to Database
connection = MongoClient('localhost', 27017)
db = connection.environmentloading

#handle to tabledata Collection
data = db.CSVdata

#reading the data from CSV and Inserting to Database
##for row in csv_f:
##    Listdata = data.insert(
##        {"column1":row[0],"column2":row[1],"column3":row[2],"column4":row[3],"column5":row[4]})
      
Listdata = data.find()

#printing the loaded data from Database
for doc in Listdata:
    pprint(doc)

connection.close() ##End the MongoDB connections

