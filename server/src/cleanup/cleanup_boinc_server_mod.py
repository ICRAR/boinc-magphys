#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2016
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
from utils.name_builder import get_archive_bucket, get_stats_archive_key
from utils.s3_helper import S3Helper

LOG = config_logger(__name__)


def correct(directory_name):
    """
    Correct the directory name so it has 0's in front of single digit numbers
    :param directory_name:
    :return:
    """
    elements = directory_name.split('_')
    if len(elements) == 7:
        add_zeros = lambda string: '{0:02d}'.format(int(string))
        return '{0}_{1}_{2}_{3}_{4}_{5}_{6}'.format(elements[0], elements[1], add_zeros(elements[2]), add_zeros(elements[3]), add_zeros(elements[4]), add_zeros(elements[5]), add_zeros(elements[6]))
    else:
        return directory_name


def move_files_to_s3(s3helper, directory_name):
    """
    Move the files to S3 for 30 days

    :param s3helper:
    :param directory_name:
    :return:
    """
    for file_name in glob.glob(os.path.join(directory_name, '*')):
        (root_directory_name, tail_directory_name) = os.path.split(directory_name)
        (root_file_name, tail_file_name) = os.path.split(file_name)
        key = get_stats_archive_key(correct(tail_directory_name), tail_file_name)
        LOG.info('Adding {0} to {1}'.format(file_name, key))
        s3helper.add_file_to_bucket(get_archive_bucket(), key, file_name)

    shutil.rmtree(directory_name, ignore_errors=True)


def archive_boinc_stats():
    """
    Clean up the BOINC stats

    Find the files and move them to S3
    :return:
    """
    delete_delay_ago = datetime.datetime.now() - datetime.timedelta(days=float(ARC_BOINC_STATISTICS_DELAY))
    LOG.info('delete_delay_ago: {0}'.format(delete_delay_ago))
    s3helper = S3Helper()
    for directory_name in glob.glob(os.path.join(POGS_BOINC_PROJECT_ROOT, 'html/stats_*')):
        if os.path.isdir(directory_name):
            directory_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(directory_name))
            LOG.info('directory: {0}, mtime: {1}'.format(directory_name, directory_mtime))
            if directory_mtime < delete_delay_ago:
                move_files_to_s3(s3helper, directory_name)


def archive_boinc_db_purge():
    """
    Clean up the BOINC DB Purge records

    Find the files and move them to S3
    :return:
    """
    delete_delay_ago = datetime.datetime.now() - datetime.timedelta(days=float(ARC_BOINC_STATISTICS_DELAY))
    LOG.info('delete_delay_ago: {0}'.format(delete_delay_ago))
    s3helper = S3Helper()
    for directory_name in glob.glob(os.path.join(POGS_BOINC_PROJECT_ROOT, 'archives/*')):
        if os.path.isdir(directory_name):
            directory_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(directory_name))
            LOG.info('directory: {0}, mtime: {1}'.format(directory_name, directory_mtime))
            if directory_mtime < delete_delay_ago:
                move_files_to_s3(s3helper, directory_name)
