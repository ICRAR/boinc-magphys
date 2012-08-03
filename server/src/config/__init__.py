"""
The Settings directory
"""
from os.path import exists
from configobj import ConfigObj

db_userid = None
db_password = None
db_hostname = None
db_name = None
db_login = None

if exists('database.settings'):
    config = ConfigObj('database.settings')
    db_userid = config['databaseUserid']
    db_password = config['databasePassword']
    db_hostname = config['databaseHostname']
    db_name = config['databaseName']
    db_login = "mysql://" + db_userid + ":" + db_password + "@" + db_hostname + "/" + db_name;

else:
    db_login = "mysql://root:@localhost/magphys"
    db_userid = 'root'
    db_password = ''
    db_hostname = 'localhost'
    db_name = 'magphys'

