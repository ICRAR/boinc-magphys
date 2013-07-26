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
Convert a FITS file ready to be converted into Work Units
"""
from __future__ import print_function
import os
import sys

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../boinc/py')))

import argparse
from Boinc import configxml
from datetime import datetime
from utils.logging_helper import config_logger
from sqlalchemy.engine import create_engine
from sqlalchemy.sql.expression import and_, func, select
from config import BOINC_DB_LOGIN, WG_THRESHOLD, WG_HIGH_WATER_MARK, DB_LOGIN, POGS_BOINC_PROJECT_ROOT
from database.boinc_database_support_core import RESULT
from database.database_support_core import REGISTER
from work_generation.fits2wu_mod import Fit2Wu, MIN_QUORUM

LOG = config_logger(__name__)
LOG.info('PYTHONPATH = {0}'.format(sys.path))

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--register', type=int, help='the registration id of a galaxy')
parser.add_argument('-l', '--limit', type=int, help='only generate N workunits from this galaxy (for testing)')
args = vars(parser.parse_args())

count = None
if args['register'] is None:
    # select count(*) from result where server_state = 2
    ENGINE = create_engine(BOINC_DB_LOGIN)
    connection = ENGINE.connect()
    count = connection.execute(select([func.count(RESULT.c.id)]).where(RESULT.c.server_state == 2)).first()[0]
    connection.close()

    LOG.info('Checking pending = %d : threshold = %d', count, WG_THRESHOLD)

LIMIT = None
if args['limit'] is not None:
    LIMIT = args['limit']

# The BOINC scripts/apps do not feel at home outside their directory
os.chdir(POGS_BOINC_PROJECT_ROOT)

# Connect to the database - the login string is set in the database package
ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()

if count is not None and count >= WG_THRESHOLD:
    LOG.info('Nothing to do')

else:
    # Get the BOINC downloads and fanout values
    boinc_config = configxml.ConfigFile().read()
    download_dir = boinc_config.config.download_dir
    fanout = long(boinc_config.config.uldl_dir_fanout)
    LOG.info("download_dir: %s, fanout: %d", download_dir, fanout)

    # Normal operation
    files_processed = 0
    if args['register'] is None:
        FILES_TO_PROCESS = WG_THRESHOLD - count + WG_HIGH_WATER_MARK

        # Get registered FITS files and generate work units until we've refilled the queue to at least the high water mark
        while files_processed < FILES_TO_PROCESS:
            LOG.info("Added %d of %d", files_processed, FILES_TO_PROCESS)
            registration = connection.execute(select([REGISTER]).where(REGISTER.c.create_time == None).order_by(REGISTER.c.priority.desc(), REGISTER.c.register_time)).first()
            if registration is None:
                LOG.info('No registrations waiting')
                break
            else:
                # As the load work unit component adds data to the data base we need autocommit on to ensure each pixel matches
                #transaction = connection.begin()
                if not os.path.isfile(registration[REGISTER.c.filename]):
                    LOG.error('The file %s does not exist', registration[REGISTER.c.filename])
                    connection.execute(REGISTER.update().where(REGISTER.c.register_id == registration[REGISTER.c.register_id]).values(create_time=datetime.now()))
                elif registration[REGISTER.c.sigma_filename] is not None and not os.path.isfile(registration[REGISTER.c.sigma_filename]):
                    LOG.error('The file %s does not exist', registration[REGISTER.c.sigma_filename])
                    connection.execute(REGISTER.update().where(REGISTER.c.register_id == registration[REGISTER.c.register_id]).values(create_time=datetime.now()))
                else:
                    LOG.info('Processing %s %d', registration[REGISTER.c.galaxy_name], registration[REGISTER.c.priority])
                    fit2wu = Fit2Wu(connection, LIMIT, download_dir, fanout)
                    (work_units_added, pixel_count) = fit2wu.process_file(registration)
                    # One WU = MIN_QUORUM Results
                    files_processed += (work_units_added * MIN_QUORUM)
                    os.remove(registration[REGISTER.c.filename])
                    if registration.sigma_filename is not None:
                        os.remove(registration[REGISTER.c.sigma_filename])
                    connection.execute(REGISTER.update().where(REGISTER.c.register_id == registration[REGISTER.c.register_id]).values(create_time=datetime.now()))

    # We want an explict galaxy to load
    else:
        registration = connection.execute(select([REGISTER]).where(and_(REGISTER.c.register_id == args['register'], REGISTER.c.create_time == None))).first()
        if registration is None:
            LOG.info('No registration waiting with the id %d', args['register'])
        else:
            # As the load work unit component adds data to the data base we need autocommit on to ensure each pixel matches
            #transaction = connection.begin()
            if not os.path.isfile(registration[REGISTER.c.filename]):
                LOG.error('The file %s does not exist', registration[REGISTER.c.filename])
                connection.execute(REGISTER.update().where(REGISTER.c.register_id == registration[REGISTER.c.register_id]).values(create_time=datetime.now()))
            elif registration[REGISTER.c.sigma_filename] is not None and not os.path.isfile(registration[REGISTER.c.sigma_filename]):
                LOG.error('The file %s does not exist', registration[REGISTER.c.sigma_filename])
                connection.execute(REGISTER.update().where(REGISTER.c.register_id == registration[REGISTER.c.register_id]).values(create_time=datetime.now()))
            else:
                LOG.info('Processing %s %d', registration[REGISTER.c.galaxy_name], registration[REGISTER.c.priority])
                fit2wu = Fit2Wu(connection, LIMIT, download_dir, fanout)
                (work_units_added, pixel_count) = fit2wu.process_file(registration)
                files_processed = work_units_added * MIN_QUORUM
                os.remove(registration[REGISTER.c.filename])
                if registration[REGISTER.c.sigma_filename] is not None:
                    os.remove(registration[REGISTER.c.sigma_filename])
                connection.execute(REGISTER.update().where(REGISTER.c.register_id == registration[REGISTER.c.register_id]).values(create_time=datetime.now()))

    LOG.info('Done - added %d Results', files_processed)

# Log how many are left in the queue
count = connection.execute(select([func.count(REGISTER.c.register_id)]).where(REGISTER.c.create_time == None)).first()[0]
LOG.info('Galaxies in queue = %d', count)

connection.close()
