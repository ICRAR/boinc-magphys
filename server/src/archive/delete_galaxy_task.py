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
Delete a galaxy and all it's related data.
"""
import logging
import os
import sys
import datetime

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../boinc/py')))
LOG.info('PYTHONPATH = {0}'.format(sys.path))

import argparse
from archive.delete_galaxy_mod import delete_galaxy
from config import DB_LOGIN, STORED, WG_DELETE_DELAY
from sqlalchemy import create_engine, and_
from sqlalchemy.sql import select
from database.database_support_core import GALAXY

# Get the arguments
parser = argparse.ArgumentParser('Delete Galaxies that have been stored')
parser.add_argument('-mod', '--mod', nargs=2, help=' M N - the modulus M to used and which value to check N ')
args = vars(parser.parse_args())

# First check the galaxy exists in the database
ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()

delete_delay_ago = datetime.datetime.now() - datetime.timedelta(days=float(WG_DELETE_DELAY))
LOG.info('Deleting {0} days ago ({1})'.format(WG_DELETE_DELAY, delete_delay_ago))
if args['mod'] is None:
    select_statement = select([GALAXY]).where(and_(GALAXY.c.status_id == STORED, GALAXY.c.status_time < delete_delay_ago)).order_by(GALAXY.c.galaxy_id)
else:
    select_statement = select([GALAXY]).where(and_(GALAXY.c.status_id == STORED, GALAXY.c.status_time < delete_delay_ago, GALAXY.c.galaxy_id % args['mod'][0] == args['mod'][1])).order_by(GALAXY.c.galaxy_id)
    LOG.info('Using modulus {0} - remainder {1}'.format(args['mod'][0], args['mod'][1]))

galaxy_ids = []
for galaxy in connection.execute(select_statement):
    galaxy_ids.append(galaxy[GALAXY.c.galaxy_id])

delete_galaxy(connection, galaxy_ids[0:20])
connection.close()
