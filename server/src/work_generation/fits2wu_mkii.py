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
import py_boinc
import signal
from Boinc import configxml
from datetime import datetime
from utils.logging_helper import config_logger
from utils.shutdown_detection import signal_handler, check_stop_trigger
from sqlalchemy.engine import create_engine
from sqlalchemy.sql.expression import func, select, or_
from config import BOINC_DB_LOGIN, WG_THRESHOLD, WG_HIGH_WATER_MARK, DB_LOGIN, POGS_BOINC_PROJECT_ROOT
from database.boinc_database_support_core import RESULT
from database.database_support_core import REGISTER, TAG_REGISTER
from work_generation.fits2wu_mod_mkii import Fit2Wu, MIN_QUORUM

# install sigint handler for shutdowns
signal.signal(signal.SIGINT, signal_handler)

LOG = config_logger(__name__)
LOG.info('PYTHONPATH = {0}'.format(sys.path))

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--limit', type=int, help='only generate N workunits from this galaxy (for testing)')
args = vars(parser.parse_args())

# select count(*) from result where server_state = 2 or server_state = 1
ENGINE = create_engine(BOINC_DB_LOGIN)
connection = ENGINE.connect()
count = connection.execute(select([func.count(RESULT.c.id)]).where(or_(RESULT.c.server_state == 2, RESULT.c.server_state == 1))).first()[0]
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

    # Database + program performance variables
    total_db_time = 0
    areaave = []
    total_boinc_db_time = 0
    areaave_boinc = []
    total_areas = 0
    total_pixels = 0

    # Open the BOINC DB
    LOG.info("Opening BOINC DB")
    return_value = py_boinc.boinc_db_open()
    if return_value != 0:
        LOG.error('Could not open BOINC DB return code: %d', return_value)

    else:
        # Normal operation
        total_work_units_added = 0
        work_units_to_be_added = WG_THRESHOLD - count + WG_HIGH_WATER_MARK

        # Get registered FITS files and generate work units until we've refilled the queue to at least the high water mark
        while total_work_units_added < work_units_to_be_added:
            if check_stop_trigger():
                LOG.info('Stop trigger identified')
                break
            LOG.info("Added %d of %d", total_work_units_added, work_units_to_be_added)
            registration = connection.execute(select([REGISTER]).where(REGISTER.c.create_time == None).order_by(REGISTER.c.priority.desc(), REGISTER.c.register_time)).first()
            if registration is None:
                LOG.info('No registrations waiting')
                break
            else:
                # As the load work unit component adds data to the data base we need autocommit on to ensure each pixel matches
                if not os.path.isfile(registration[REGISTER.c.filename]):
                    LOG.error('The file %s does not exist', registration[REGISTER.c.filename])
                    connection.execute(REGISTER.update().where(REGISTER.c.register_id == registration[REGISTER.c.register_id]).values(create_time=datetime.now()))
                elif registration[REGISTER.c.sigma_filename] is not None and not os.path.isfile(registration[REGISTER.c.sigma_filename]):
                    LOG.error('The file %s does not exist', registration[REGISTER.c.sigma_filename])
                    connection.execute(REGISTER.update().where(REGISTER.c.register_id == registration[REGISTER.c.register_id]).values(create_time=datetime.now()))
                else:
                    LOG.info('Processing {0} {1} {2}'.format(registration[REGISTER.c.galaxy_name], registration[REGISTER.c.priority], registration[REGISTER.c.register_id]))

                    fit2wu = Fit2Wu(
                        connection,
                        download_dir,
                        fanout)
                    try:
                        (work_units_added, pixel_count, sum, ave, bsum, bave, areas, pixels) = fit2wu.process_file(registration)

                        # Calculate performance information
                        total_db_time += sum
                        total_boinc_db_time += bsum
                        areaave.append(ave)
                        areaave_boinc.append(bave)
                        total_areas += areas
                        total_pixels += pixels

                        total_work_units_added += (work_units_added * MIN_QUORUM)
                    except Exception:
                        LOG.exception('An error occurred while processing {0}'.format(registration[REGISTER.c.galaxy_name]))
                        break
                    # One WU = MIN_QUORUM Results

                    if os.path.exists(registration[REGISTER.c.filename]):
                        os.remove(registration[REGISTER.c.filename])
                    if registration.sigma_filename is not None and os.path.exists(registration.sigma_filename):
                        os.remove(registration[REGISTER.c.sigma_filename])
                    connection.execute(REGISTER.update().where(REGISTER.c.register_id == registration[REGISTER.c.register_id]).values(create_time=datetime.now()))
                connection.execute(TAG_REGISTER.delete().where(TAG_REGISTER.c.register_id == registration[REGISTER.c.register_id]))

        LOG.info('Total areas added {0}, pixels added {1}'.format(total_areas, total_pixels))
        if len(areaave) > 0:
            LOG.info('Total db time: {0}'.format(total_db_time))
            asum = 0
            for rtime in areaave:
                asum += rtime
            LOG.info('Average time per transaction: {0}'.format(asum / len(areaave)))

            LOG.info('Total BOINC db time: {0}'.format(total_boinc_db_time))
            asum_boinc = 0
            for rtime in areaave_boinc:
                asum_boinc += rtime
            LOG.info('Average BOINC db time per transaction: {0}'.format(asum_boinc / len(areaave_boinc)))

        LOG.info('Done - added %d Results', total_work_units_added)

    # Closing BOINC DB
    if return_value == 0:
        LOG.info('Closing BOINC DB')
        return_value = py_boinc.boinc_db_close()

# Log how many are left in the queue
count = connection.execute(select([func.count(REGISTER.c.register_id)]).where(REGISTER.c.create_time == None)).first()[0]
LOG.info('Galaxies in queue = %d', count)

connection.close()
