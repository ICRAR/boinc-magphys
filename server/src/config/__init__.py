#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
"""
The configuration directory
"""
from os.path import exists, dirname
from configobj import ConfigObj

############### DB SETTINGS ###############
DB_USER_ID = None
DB_PASSWORD = None
DB_HOSTNAME = None
DB_NAME = None
BOINC_DB_NAME = None
DB_LOGIN = None
BOINC_DB_LOGIN = None
PLEIADES_DB_LOGIN = None

db_file_name = dirname(__file__) + '/database.settings'
if exists(db_file_name):
    config = ConfigObj(db_file_name)
    DB_USER_ID = config['databaseUserid']
    DB_PASSWORD = config['databasePassword']
    DB_HOSTNAME = config['databaseHostname']
    DB_NAME = config['databaseName']
    BOINC_DB_NAME = config['boincDatabaseName']
    DB_LOGIN = "mysql://" + DB_USER_ID + ":" + DB_PASSWORD + "@" + DB_HOSTNAME + "/" + DB_NAME
    BOINC_DB_LOGIN = "mysql://" + DB_USER_ID + ":" + DB_PASSWORD + "@" + DB_HOSTNAME + "/" + BOINC_DB_NAME
    PLEIADES_DB_LOGIN = "mysql://" + DB_USER_ID + ":" + DB_PASSWORD + "@pleiades01.icrar.org/" + DB_NAME

else:
    DB_LOGIN = "mysql://root:@localhost/magphys"
    DB_USER_ID = 'root'
    DB_PASSWORD = ''
    DB_HOSTNAME = 'localhost'
    DB_NAME = 'magphys'
    boincDatabaseName = 'pogs'
    BOINC_DB_LOGIN = "mysql://root:@localhost/pogs"

############### Django Settings ###############

DJANGO_TEMPLATE_DIR = None
DJANGO_IMAGE_DIR = None
DJANGO_FILE_NAME = dirname(__file__) + '/django.settings'
if exists(DJANGO_FILE_NAME):
    config = ConfigObj(DJANGO_FILE_NAME)
    DJANGO_TEMPLATE_DIR = config['template_dir']
    DJANGO_IMAGE_DIR = config['image_dir']
else:
    DJANGO_TEMPLATE_DIR = '/Users/rob/development/boinc-magphys/server/src/templates'
    DJANGO_IMAGE_DIR = '/Users/rob/magphys/POGS_NGC1209'

############### Work Generation Settings ###############

work_generation_file_name = dirname(__file__) + '/work_generation.settings'
WG_IMAGE_DIRECTORY = None
WG_ROW_HEIGHT = None
WG_MIN_PIXELS_PER_FILE = None
WG_THRESHOLD = None
WG_HIGH_WATER_MARK = None
WG_BOINC_PROJECT_ROOT = None
WG_REPORT_DEADLINE = None
if exists(work_generation_file_name):
    config = ConfigObj(work_generation_file_name)
    WG_IMAGE_DIRECTORY = config['image_directory']
    WG_MIN_PIXELS_PER_FILE = int(config['min_pixels_per_file'])
    WG_ROW_HEIGHT = int(config['row_height'])
    WG_THRESHOLD = int(config['threshold'])
    WG_HIGH_WATER_MARK = int(config['high_water_mark'])
    WG_BOINC_PROJECT_ROOT = config['boinc_project_root']
    WG_REPORT_DEADLINE = int(config['report_deadline'])
else:
    WG_IMAGE_DIRECTORY = '/home/ec2-user/galaxyImages'
    WG_MIN_PIXELS_PER_FILE = 15
    WG_ROW_HEIGHT = 10
    WG_THRESHOLD = 1500
    WG_HIGH_WATER_MARK = 3000
    WG_REPORT_DEADLINE = 7

############### Assimilator Settings ###############

# Any probability in the pixel histogram less than this is considered to be 0 and ignored
MIN_HIST_VALUE = 0.01
