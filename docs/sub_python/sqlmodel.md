# SQLMODEL

sqlmodel is claimed to be very easy to use utility to connect data to various databases and pydantic data models. This documents the learnings

##	Introduction


## Usecases

### Python Design First

Python Design First is a generic assumption of writing code. The typical steps are given below:
- Create python sqlmodel objects
- Save the objects to a database without existing table
- Upon save, the objects will create a database table with associated data type definitions. 
- SQLALchemy helps definte these appropriate definitions

For example code, see 

### Database First Design

Database First Design is another generic assumption of writing code. The typical steps are given below:
- Create engine/connection to database
- Read a table
- Review the data and data types of the sqlmodel objects

### Updating database data

https://sqlmodel.tiangolo.com/tutorial/update/

upsert?