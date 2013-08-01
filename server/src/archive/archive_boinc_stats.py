#! /usr/bin/env python2.7
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
Archive the stats stored in .../html/stats_archive to S3 if they are old enough
"""
import os
import sys

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../boinc/py')))

import argparse
from utils.logging_helper import config_logger, add_file_handler_to_root
from utils.s3_helper import S3Helper
from archive.archive_boinc_stats_mod import process_ami, process_boinc
from utils.ec2_helper import EC2Helper
from utils.name_builder import get_archive_bucket, get_log_archive_key, get_ami_log_file
from utils.sanity_checks import pass_sanity_checks

LOG = config_logger(__name__)

parser = argparse.ArgumentParser('Archive BOINC statistics to S3')
parser.add_argument('option', choices=['boinc','ami'], help='are we running on the BOINC server or the AMI server')
args = vars(parser.parse_args())

if args['option'] == 'boinc':
    LOG.info('PYTHONPATH = {0}'.format(sys.path))
    # We're running from the BOINC server
    process_boinc()
else:
    # We're running from a specially created AMI
    filename, full_filename = get_ami_log_file('archive_boinc_stats')
    add_file_handler_to_root(full_filename)
    LOG.info('PYTHONPATH = {0}'.format(sys.path))
    LOG.info('About to perform sanity checks')
    if pass_sanity_checks():
        process_ami()
    else:
        LOG.error('Failed to pass sanity tests')

    # Try copying the log file to S3
    try:
        LOG.info('About to copy the log file')
        s3helper = S3Helper()
        s3helper.add_file_to_bucket(get_archive_bucket(), get_log_archive_key('archive_boinc_stats', filename), full_filename, True)
        #os.remove(full_filename)
    except:
        LOG.exception('Failed to copy the log file')

    ec2_helper = EC2Helper()
    ec2_helper.release_public_ip()
