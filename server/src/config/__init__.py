#
#    Copyright (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
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
    WG_MIN_PIXELS_PER_FILE = []
    for size in config['min_pixels_per_file']:
        WG_MIN_PIXELS_PER_FILE.append(int(size))

    WG_ROW_HEIGHT = int(config['row_height'])
    WG_THRESHOLD = int(config['threshold'])
    WG_HIGH_WATER_MARK = int(config['high_water_mark'])
    WG_REPORT_DEADLINE = int(config['report_deadline'])
    WG_PIXEL_COMMIT_THRESHOLD = int(config['pixel_commit_threshold'])
    WG_SIZE_CLASS = []
    for size in config['size_classes']:
        WG_SIZE_CLASS.append(int(size))
    RADIAL_AREA_SIZE = int(config['radial_area_size'])

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

    ############### EC2 IPs ###############
    EC2_IP_ARCHIVE_ADDRESSES = {}
    EC2_IP_BUILD_IMAGE_ADDRESSES = {}

    i = 0
    for ip in config['ec2_ips_archive']:
        EC2_IP_ARCHIVE_ADDRESSES[i] = ip
        i += 1

    i = 0
    for ip in config['ec2_ips_build_image']:
        EC2_IP_BUILD_IMAGE_ADDRESSES[i] = ip
        i += 1

    ############### HDF5 to FITS ###############
    S3_FILE_RESTORE_TIME = int(config['s3_file_restore_time'])  # How long a file should be restored from glacier for (days)
    GALAXY_EMAIL_THRESHOLD = float(config['galaxy_email_threshold'])  # What % of galaxies from an order should be avaiable before an email is sent


############### Archive Settings ###############

# Any probability in the pixel histogram less than this is considered to be 0 and ignored
MIN_HIST_VALUE = 0.01
OUTPUT_FORMAT_1_00 = 'Version 1.00'
OUTPUT_FORMAT_1_01 = 'Version 1.01'
OUTPUT_FORMAT_1_02 = 'Version 1.02'
OUTPUT_FORMAT_1_03 = 'Version 1.03'
OUTPUT_FORMAT_1_04 = 'Version 1.04'

PARAMETER_TYPES = ['f_mu (SFH)',
                   'f_mu (IR)',
                   'mu parameter',
                   'tau_V',
                   'sSFR_0.1Gyr',
                   'M(stars)',
                   'Ldust',
                   'T_C^ISM',
                   'T_W^BC',
                   'xi_C^tot',
                   'xi_PAH^tot',
                   'xi_MIR^tot',
                   'xi_W^tot',
                   'tau_V^ISM',
                   'M(dust)',
                   'SFR_0.1Gyr']

NUMBER_PARAMETERS = 16
NUMBER_IMAGES = 7
HISTOGRAM_BLOCK_SIZE = 1000000
MAX_X_Y_BLOCK = 1024

INDEX_BEST_FIT = 0
INDEX_PERCENTILE_50 = 1
INDEX_HIGHEST_PROB_BIN = 2
INDEX_PERCENTILE_2_5 = 3
INDEX_PERCENTILE_16 = 4
INDEX_PERCENTILE_84 = 5
INDEX_PERCENTILE_97_5 = 6

INDEX_F_MU_SFH = 0
INDEX_F_MU_IR = 1
INDEX_MU_PARAMETER = 2
INDEX_TAU_V = 3
INDEX_SSFR_0_1GYR = 4
INDEX_M_STARS = 5
INDEX_L_DUST = 6
INDEX_T_C_ISM = 7
INDEX_T_W_BC = 8
INDEX_XI_C_TOT = 9
INDEX_XI_PAH_TOT = 10
INDEX_XI_MIR_TOT = 11
INDEX_XI_W_TOT = 12
INDEX_TAU_V_ISM = 13
INDEX_M_DUST = 14
INDEX_SFR_0_1GYR = 15

############### DB Settings ###############
COMPUTING = 0
PROCESSED = 1
ARCHIVED = 2
STORED = 3
DELETED = 4
