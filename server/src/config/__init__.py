"""
The configuration directory
"""
from os.path import exists, dirname
from configobj import ConfigObj


############### DB SETTINGS ###############
db_userid = None
db_password = None
db_hostname = None
db_name = None
db_login = None

db_file_name = dirname(__file__) + '/database.settings'
if exists(db_file_name):
    config = ConfigObj(db_file_name)
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

############### Django Settings ###############

django_template_dir = None
django_image_dir = None
django_file_name = dirname(__file__) + '/django.settings'
if exists(django_file_name):
    config = ConfigObj(django_file_name)
    django_template_dir = config['template_dir']
    django_image_dir = config['image_dir']
else:
    django_template_dir = '/Users/rob/development/boinc-magphys/server/src/templates'
    django_image_dir = '/Users/rob/magphys/POGS_NGC1209'
