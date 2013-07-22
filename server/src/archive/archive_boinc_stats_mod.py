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
The code to archive the BOINC statistics
"""
import glob
import logging
import os
import datetime
from config import POGS_BOINC_PROJECT_ROOT, ARC_BOINC_STATISTICS_DELAY
from utils.ec2_helper import get_ec2_connection, get_all_instances
from utils.name_builder import get_glacier_archive_bucket, get_boinc_archive_key
from utils.s3_helper import add_file_to_bucket

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

ARCHIVE_DATA = 'archive_data'

def instance_running(ec2_connection):
    """
    Do we have an instance running

    :param ec2_connection:
    :return:
    """
    instances = get_all_instances(ec2_connection, ARCHIVE_DATA)
    return len(instances) > 0


def process_boinc():
    """
    We're running the process on the BOINC server.

    Check if an instance is still running, if not start it up.
    :return:
    """
    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    ec2_connection = get_ec2_connection()

    if instance_running(ec2_connection):
        LOG.info('A previous instance is still running')
    else:
        LOG.info('Starting up the instance')
        run_instance(ec2_connection)


def move_files_to_s3(directory_name):
    for file_name in glob.glob(os.path.join(directory_name, '*')):
        bucket = get_glacier_archive_bucket()
        (root_directory_name, tail_directory_name) = os.path.split(directory_name)
        (root_file_name, tail_file_name) = os.path.split(file_name)
        key = get_boinc_archive_key(tail_directory_name, tail_file_name)
        add_file_to_bucket(bucket, key, file_name)

    os.removedirs(directory_name)


def process_ami(logging_file_handler):
    """
    We're running on the AMI instance - so actually do the work

    Find the files and move them to S3
    :return:
    """
    LOG.addHandler(logging_file_handler)
    delete_delay_ago = datetime.datetime.now() - datetime.timedelta(days=float(ARC_BOINC_STATISTICS_DELAY))
    LOG.info('delete_delay_ago: {0}'.format(delete_delay_ago))
    for directory_name in glob.glob(os.path.join(POGS_BOINC_PROJECT_ROOT, 'html/stats_archive/*')):
        if os.path.isdir(directory_name):
            directory_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(directory_name))
            LOG.info('directory: {0}, mtime: {1}'.format(directory_name, directory_mtime))
            if directory_mtime < delete_delay_ago:
                move_files_to_s3(directory_name)
