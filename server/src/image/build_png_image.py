#! /usr/bin/env python2.7
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
Build a PNG image from the data in the database
"""
import os
import sys

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '../')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../boinc/py')))

import argparse
from utils.logging_helper import config_logger, add_special_handler_to_root
from utils.ec2_helper import EC2Helper
from utils.sanity_checks import pass_sanity_checks
from image.build_png_image_mod import build_png_image_boinc, build_png_image_ami
from config import LOGGER_SERVER_ADDRESS, LOGGER_SERVER_PORT

import time

LOG = config_logger(__name__)

parser = argparse.ArgumentParser('Build the intermediary images to show how the work is progressing')
parser.add_argument('option', choices=['boinc','ami'], help='are we running on the BOINC server or the AMI server')
args = vars(parser.parse_args())

if args['option'] == 'boinc':
    LOG.info('PYTHONPATH = {0}'.format(sys.path))
    # We're running from the BOINC server
    build_png_image_boinc()
else:
    # We're running from a specially created AMI
    LOG.info('Attempting to create socket handler...')
    add_special_handler_to_root(LOGGER_SERVER_ADDRESS, LOGGER_SERVER_PORT, 'build_png_image_AMI')

    LOG.info('Socket handler created, logs should appear on logging server')
    LOG.info('Logging server host: {0}'.format(LOGGER_SERVER_ADDRESS))
    LOG.info('Logging server port: {0}'.format(str(LOGGER_SERVER_PORT)))

    LOG.info('PYTHONPATH = {0}'.format(sys.path))
    LOG.info('About to perform sanity checks')
    if pass_sanity_checks():
        build_png_image_ami()
    else:
        LOG.error('Failed to pass sanity tests')

LOG.info('All done.')
