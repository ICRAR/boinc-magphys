"""
Define how to connect to the database
"""

from os.path import exists
from configobj import ConfigObj

if exists('../settings/database.settings'):
    try:
        config = ConfigObj('../settings/database.settings')
        userid = config['databaseUserid']
        password = config['databasePassword']
        hostname = config['databaseHostname']
        database_name = config['databaseName']
        login = "mysql://" + userid + ":" + password + "@" + hostname + "/" + database_name;
    except NameError as e:
        login = "mysql://root:@localhost/magphys"

else:
    login = "mysql://root:@localhost/magphys"
