import mysql.connector
import xlrd

# Open the workbook and define the worksheet
book = xlrd.open_workbook("C:\\Users\\AceEngineer-002\\Desktop\\Today\\Test.xls")

sheet = book.sheet_by_index(0)


# Establish a MySQL Connection
database = mysql.connector.connect(
    host="localhost", user="root", passwd="Root", db="ace"
)

# Get the cursor, which is used to traverse the database, line by line
mycursor = database.cursor()

# Create the INSERT INTO sql query
query = """INSERT INTO customers(ID,Name,Age,Balance)VALUES(%s,%s,%s,%s)"""

# Create a for loop to iterate through each row in the xls file, starting from row 2
for r in range(1, sheet.nrows):
    ID = sheet.cell(r, 0).value
    Name = sheet.cell(r, 1).value
    Age = sheet.cell(r, 2).value
    Balance = sheet.cell(r, 3).value

    # Assign values from each row
    values = (ID, Name, Age, Balance)

    # Execute sql query
    mycursor.execute(query, values)
# Close the cursor
mycursor.close()

# Commit the transaction
database.commit()
# Close the database connection
database.close()
# Print results
print("")
print("Data Imported successfully!!!")
print("")
columns = str(sheet.ncols)
rows = str(sheet.nrows)
print("Summary of data imported: " + columns + "columns and " + rows + " rows")
