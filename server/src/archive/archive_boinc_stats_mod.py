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
import os
import datetime
import shutil
from utils.logging_helper import config_logger
from config import POGS_BOINC_PROJECT_ROOT, ARC_BOINC_STATISTICS_DELAY
from utils.ec2_helper import EC2Helper
from utils.name_builder import get_archive_bucket, get_stats_archive_key
from utils.s3_helper import S3Helper

LOG = config_logger(__name__)

BOINC_VALUE = 'archive_data'
USER_DATA = '''#!/bin/bash

# Sleep for a while to let everything settle down
sleep 10s

# Has the NFS mounted properly?
if [ -d '/home/ec2-user/boinc-magphys/server' ]
then
    # We are root so we have to run this via sudo to get access to the ec2-user details
    su -l ec2-user -c 'python2.7 /home/ec2-user/boinc-magphys/server/src/archive/archive_boinc_stats.py ami'
fi

# All done terminate
shutdown -h now
'''


def process_boinc():
    """
    We're running the process on the BOINC server.

    Check if an instance is still running, if not start it up.
    :return:
    """
    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    ec2_helper = EC2Helper()

    if ec2_helper.boinc_instance_running(BOINC_VALUE):
        LOG.info('A previous instance is still running')
    else:
        LOG.info('Starting up the instance')
        ec2_helper.run_instance(USER_DATA, BOINC_VALUE)


def move_files_to_s3(s3helper, directory_name):
    for file_name in glob.glob(os.path.join(directory_name, '*')):
        (root_directory_name, tail_directory_name) = os.path.split(directory_name)
        (root_file_name, tail_file_name) = os.path.split(file_name)
        key = get_stats_archive_key(tail_directory_name, tail_file_name)
        LOG.info('Adding {0} to {1}'.format(file_name, key))
        s3helper.add_file_to_bucket(get_archive_bucket(), key, file_name)

    shutil.rmtree(directory_name, ignore_errors=True)


def process_ami():
    """
    We're running on the AMI instance - so actually do the work

    Find the files and move them to S3
    :return:
    """
    delete_delay_ago = datetime.datetime.now() - datetime.timedelta(days=float(ARC_BOINC_STATISTICS_DELAY))
    LOG.info('delete_delay_ago: {0}'.format(delete_delay_ago))
    s3helper = S3Helper()
    for directory_name in glob.glob(os.path.join(POGS_BOINC_PROJECT_ROOT, 'html/stats_archive/*')):
        if os.path.isdir(directory_name):
            directory_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(directory_name))
            LOG.info('directory: {0}, mtime: {1}'.format(directory_name, directory_mtime))
            if directory_mtime < delete_delay_ago:
                move_files_to_s3(s3helper, directory_name)
