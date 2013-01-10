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
Load the run details into the database
"""
import argparse
from decimal import Decimal
import logging
import os
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import select, func
from config import DB_LOGIN
from database.database_support_core import RUN, FILTER, RUN_FILE, RUN_FILTER

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser()
parser.add_argument('run_id', type=int, nargs=1, help='the run id to be used')
parser.add_argument('dir', nargs=1, help='the directory containing the files')
parser.add_argument('url_stem', nargs=1, help='the stem of the URL')
parser.add_argument('description', nargs=1, help='a short description of the run')
parser.add_argument('fpops_est', type=float, nargs=1, help='the GFlops estimate')
parser.add_argument('cobblestone_factor', type=float, nargs=1, help='the cobblestone scaling factor')

args = vars(parser.parse_args())

RUN_ID = args['run_id'][0]
INPUT_DIR = args['dir'][0]
URL_STEM = args['url_stem'][0]
DESCRIPTION = args['description'][0]
FPOPS_EST = args['fpops_est'][0]
COBBLESTONE_FACTOR = args['cobblestone_factor'][0]

# Connect to the database - the login string is set in the database package
ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()

# Check things exist
errors = []

if os.path.isdir(INPUT_DIR):
    # Is the filters file there
    if not os.path.isfile('{0}/filters.dat'.format(INPUT_DIR)):
        errors.append('The file {0}/filters.dat does not exist'.format(INPUT_DIR))

    if not os.path.isfile('{0}/file_details.dat'.format(INPUT_DIR)):
        errors.append('The file {0}/file_details.dat does not exist'.format(INPUT_DIR))

    count = connection.execute(select([func.count(RUN.c.run_id)]).where(RUN.c.run_id == RUN_ID)).first()
    if count[0] > 0:
        errors.append('The run id {0} already exists'. format(RUN_ID))

else:
    errors.append('The directory {0} does not exist.'.format(INPUT_DIR))

# we have errors
if len(errors) > 0:
    for error in errors:
        LOG.error(error)

else:
    # Now we build everything
    transaction = connection.begin()
    commit = True
    # Build the run
    connection.execute(RUN.insert().values(run_id = RUN_ID,
        directory          = INPUT_DIR,
        short_description  = DESCRIPTION,
        long_description   = DESCRIPTION,
        fpops_est          = FPOPS_EST,
        cobblestone_factor = COBBLESTONE_FACTOR))

    # Read the filters file
    with open('{0}/filters.dat'.format(INPUT_DIR), 'rb') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#'):
                # It's a comment so we can ignore it
                pass
            elif len(line) > 0:
                details = line.split()

                # We should have 4 items
                if len(details) == 4:
                    filter = connection.execute(select([FILTER]).where(FILTER.c.filter_number == details[2])).first()
                    if filter is None:
                        commit = False
                        LOG.error('The filter {0} {1} does not exist in the database'.format(details[0], details[2]))
                    else:
                        LOG.info('Adding the filter %s %s', details[0], details[2])
                        connection.execute(RUN_FILTER.insert().values(run_id = RUN_ID, filter_id = filter[FILTER.c.filter_id]))

    # Add the file details
    with open('{0}/file_details.dat'.format(INPUT_DIR), 'rb') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#'):
                # It's a comment so we can ignore it
                pass
            elif len(line) > 0:
                details = line.split()

                # We should have 5 items
                if len(details) == 5:
                    if URL_STEM.endswith('/'):
                        file_name = '{0}{1}'.format(URL_STEM, details[0])
                    else:
                        file_name = '{0}/{1}'.format(URL_STEM, details[0])
                    connection.execute(RUN_FILE.insert().values(run_id = RUN_ID,
                        file_name = file_name,
                        file_type = int(details[1]),
                        md5_hash = details[2],
                        redshift = Decimal(details[3]),
                        size = long(details[4])))
                    LOG.info('Adding %s', details[0])

    if commit:
        transaction.commit()
    else:
        transaction.rollback()

connection.close()
