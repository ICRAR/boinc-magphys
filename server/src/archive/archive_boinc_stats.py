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
Archive the stats stored in .../html/stats_archive to S3
"""
import logging
import os
import sys

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../boinc/py')))

import argparse
import datetime
from utils.s3_helper import S3Helper
from archive.archive_boinc_stats_mod import process_ami, process_boinc, BOINC_VALUE
from utils.ec2_helper import EC2Helper
from utils.name_builder import get_archive_bucket, get_log_archive_key
from utils.sanity_checks import pass_sanity_checks

parser = argparse.ArgumentParser('Archive BOINC statistics to S3')
parser.add_argument('option', choices=['boinc','ami'], help='are we running on the BOINC server or the AMI server')
args = vars(parser.parse_args())

filename = '{0}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
full_filename = '/home/ec2-user/logs_ami/archive_boinc_stats{0}'.format(filename)

if args['option'] == 'boinc':
    LOG.info('PYTHONPATH = {0}'.format(sys.path))
    # We're running from the BOINC server
    process_boinc(full_filename)
else:
    # We're running from a specially created AMI
    LOG.info('PYTHONPATH = {0}'.format(sys.path))
    LOG.info('About to perform sanity checks')
    if pass_sanity_checks():
        process_ami()
    else:
        LOG.error('Failed to pass sanity tests')

    # Try copying the log file to S3
    try:
        s3helper = S3Helper()
        bucket = s3helper.get_bucket(get_archive_bucket())
        s3helper.add_file_to_bucket(bucket, get_log_archive_key('archive_boinc_stats', filename), full_filename, True)
        os.remove(full_filename)
    except:
        pass

    ec2_helper = EC2Helper()
    ec2_helper.release_public_ip(BOINC_VALUE)
