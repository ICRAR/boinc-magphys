#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013
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

############### AWS Instance Tags we use ###############
BUILD_PNG_IMAGE = 'build_png_image'
ORIGINAL_IMAGE_CHECKED = 'original_image_checked'

config_file_name = dirname(__file__) + '/pogs.settings'
if exists(config_file_name):
    config = ConfigObj(config_file_name)
    ############### Database Settings ###############
    DB_USER_ID = config['databaseUserid']
    DB_PASSWORD = config['databasePassword']
    DB_HOSTNAME = config['databaseHostname']
    DB_NAME = config['databaseName']
    BOINC_DB_NAME = config['boincDatabaseName']
    DB_LOGIN = "mysql://" + DB_USER_ID + ":" + DB_PASSWORD + "@" + DB_HOSTNAME + "/" + DB_NAME
    BOINC_DB_LOGIN = "mysql://" + DB_USER_ID + ":" + DB_PASSWORD + "@" + DB_HOSTNAME + "/" + BOINC_DB_NAME

    ############### Work Generation Settings ###############
    WG_MIN_PIXELS_PER_FILE = int(config['min_pixels_per_file'])
    WG_ROW_HEIGHT = int(config['row_height'])
    WG_THRESHOLD = int(config['threshold'])
    WG_HIGH_WATER_MARK = int(config['high_water_mark'])
    WG_REPORT_DEADLINE = int(config['report_deadline'])

    ############### ARCHIVE Settings ###############
    ARC_DELETE_DELAY = config['delete_delay']
    ARC_BOINC_STATISTICS_DELAY = config['boinc_statistics_delay']
    HDF5_OUTPUT_DIRECTORY = config['hdf5_output_directory']

    ############### Global Settings ###############
    POGS_TMP = config['tmp']
    POGS_PROJECT_NAME = config['project_name']
    POGS_BOINC_PROJECT_ROOT = config['boinc_project_root']

    ############### AWS Settings ###############
    AWS_AMI_ID = config['ami_id']
    AWS_KEY_NAME = config['key_name']
    AWS_SECURITY_GROUPS = config['security_groups']
    AWS_SUBNET_IDS = config['subnet_ids']

    BUILD_PNG_IMAGE_DICT = config[BUILD_PNG_IMAGE]
    ORIGINAL_IMAGE_CHECKED_DICT = config[ORIGINAL_IMAGE_CHECKED]
    ARCHIVE_DATA_DICT = config['archive_data']
    SPOT_PRICE_MULTIPLIER = float(config['spot_price_multiplier'])

    AWS_SUBNET_DICT = {}
    for subnet_id in AWS_SUBNET_IDS:
        AWS_SUBNET_DICT[subnet_id] = config[subnet_id]

    ############### Logging Server ###############
    LOGGER_SERVER_PORT = int(config['logger_port'])
    LOGGER_SERVER_ADDRESS = config['logger_address']
    LOGGER_MAX_CONNECTION_REQUESTS = int(config['logger_max_requests'])
    LOGGER_LOG_DIRECTORY = config['logger_directory']

############### Archive Settings ###############

# Any probability in the pixel histogram less than this is considered to be 0 and ignored
MIN_HIST_VALUE = 0.01

############### DB Settings ###############
COMPUTING = 0
PROCESSED = 1
ARCHIVED = 2
STORED = 3
DELETED = 4

