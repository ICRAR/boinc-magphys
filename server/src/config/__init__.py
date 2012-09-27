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
boinc_db_name = None
db_login = None
boinc_db_login = None

db_file_name = dirname(__file__) + '/database.settings'
if exists(db_file_name):
    config = ConfigObj(db_file_name)
    db_userid = config['databaseUserid']
    db_password = config['databasePassword']
    db_hostname = config['databaseHostname']
    db_name = config['databaseName']
    boinc_db_name = config['boincDatabaseName']
    db_login = "mysql://" + db_userid + ":" + db_password + "@" + db_hostname + "/" + db_name
    boinc_db_login = "mysql://" + db_userid + ":" + db_password + "@" + db_hostname + "/" + boinc_db_name

else:
    db_login = "mysql://root:@localhost/magphys"
    db_userid = 'root'
    db_password = ''
    db_hostname = 'localhost'
    db_name = 'magphys'
    boincDatabaseName = 'pogs'
    boinc_db_login = "mysql://root:@localhost/pogs"

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

############### Work Generation Settings ###############

work_generation_file_name = dirname(__file__) + '/work_generation.settings'
wg_image_directory = None
wg_row_height = None
wg_min_pixels_per_file = None
wg_threshold = None
wg_high_water_mark = None
wg_boinc_project_root = None
if exists(work_generation_file_name):
    config = ConfigObj(work_generation_file_name)
    wg_image_directory = config['image_directory']
    wg_min_pixels_per_file = int(config['min_pixels_per_file'])
    wg_row_height = int(config['row_height'])
    wg_threshold = int(config['threshold'])
    wg_high_water_mark = int(config['high_water_mark'])
    wg_boinc_project_root = config['boinc_project_root']
else:
    wg_image_directory = '/home/ec2-user/galaxyImages'
    wg_min_pixels_per_file = 15
    wg_row_height = 10
    wg_threshold = 1500
    wg_high_water_mark = 3000
