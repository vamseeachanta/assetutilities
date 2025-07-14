import _mysql

serverType1 = "MYSQL"
serverName1 = "localhost"
serverPort1 = 3306
userName1 = "AceEngineer"
userPassword1 = "Ace@DataWare!2020"
database1 = "krishna-d"

db = _mysql.connect(
    host=serverName1,
    port=serverPort1,
    user=userName1,
    passwd=userPassword1,
    db=database1,
)
# cur = db.cursor()
print("db connection successful using _mysql")
