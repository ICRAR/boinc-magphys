"""
Define how to connect to the database
"""

#databaseUserid
#databasePassword
#databaseHostname
#databaseName

login = "mysql://root:@localhost/magphys"
try:
    login = "mysql://" + databaseUserid + ":" + databasePassword + "@" + databaseHostname + "/" + databaseName;
except NameError as e:
    login = "mysql://root:@localhost/magphys"
