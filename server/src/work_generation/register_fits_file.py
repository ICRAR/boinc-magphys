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
Register a FITS file ready to be converted into Work Units
"""
import argparse
import sys
from datetime import datetime
from sqlalchemy import select
from utils.logging_helper import config_logger
import os
from sqlalchemy.engine import create_engine
from config import DB_LOGIN
from database.database_support_core import REGISTER, TAG_REGISTER, TAG

LOG = config_logger(__name__)
LOG.info('PYTHONPATH = {0}'.format(sys.path))

parser = argparse.ArgumentParser()
parser.add_argument('FITS_file', nargs=1, help='the input FITS file containing the galaxy')
parser.add_argument('redshift', type=float, nargs=1, help='the redshift of the galaxy')
parser.add_argument('galaxy_name', nargs=1, help='the name of the galaxy')
parser.add_argument('type', nargs=1, help='the hubble type')
parser.add_argument('sigma', nargs=1, help='the error in the observations or the file with the per pixel error')
parser.add_argument('priority', type=int, nargs=1, help='the higher the number the higher the priority')
parser.add_argument('run_id', type=int, nargs=1, help='the run id to be used')
parser.add_argument('tags', nargs='*', help='any tags to be associated with the galaxy')

args = vars(parser.parse_args())

REDSHIFT = args['redshift'][0]
INPUT_FILE = args['FITS_file'][0]
GALAXY_NAME = args['galaxy_name'][0]
GALAXY_TYPE = args['type'][0]
PRIORITY = args['priority'][0]
SIGMA = args['sigma'][0]
RUN_ID = args['run_id'][0]
TAGS = args['tags']

# Make sure the file exists
if not os.path.isfile(INPUT_FILE):
    LOG.error('The file %s does not exist', INPUT_FILE)
    exit(1)

# Connect to the database - the login string is set in the database package
ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()
transaction = connection.begin()

# If it is a float store it as the sigma otherwise assume it is a string pointing to a file containing the sigmas
try:
    sigma = float(SIGMA)
    sigma_filename = None
except ValueError:
    sigma = 0.0
    sigma_filename = SIGMA

result = connection.execute(REGISTER.insert(),
                            galaxy_name=GALAXY_NAME,
                            redshift=REDSHIFT,
                            galaxy_type=GALAXY_TYPE,
                            filename=INPUT_FILE,
                            priority=PRIORITY,
                            register_time=datetime.now(),
                            run_id=RUN_ID,
                            sigma=sigma,
                            sigma_filename=sigma_filename)

register_id = result.inserted_primary_key[0]

# Get the tag ids
tag_ids = set()
for tag_text in TAGS:
    tag_text = tag_text.strip()
    if len(tag) > 0:
        tag = connection.execute(select([TAG]).where(TAG.c.tag_text == tag_text)).first()
        if tag is None:
            tag_id = tag[TAG.c.tag_id]
            result = connection.execute(TAG.insert(),
                                        tag_text=tag)
            tag_id = result.inserted_primary_key[0]
        else:
            tag_id = tag[TAG.c.tag_id]

        tag_ids.add(tag_id)

# Add the tag ids
for tag_id in tag_ids:
    connection.execute(TAG_REGISTER.insert(),
                       tag_id=tag_id,
                       register_id=register_id)

transaction.commit()

LOG.info('Registered %s %s %f %s %d %d', GALAXY_NAME, GALAXY_TYPE, REDSHIFT, INPUT_FILE, PRIORITY, RUN_ID)
