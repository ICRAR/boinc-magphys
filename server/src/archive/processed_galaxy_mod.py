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
The function used to process a galaxy
"""
import datetime
from sqlalchemy import select
from database.database_support_core import AREA, GALAXY
from sqlalchemy.engine import create_engine
from config import BOINC_DB_LOGIN, PROCESSED, COMPUTING
from database.boinc_database_support_core import RESULT
from utils.logging_helper import config_logger

LOG = config_logger(__name__)


def build_key(galaxy_name, galaxy_id):
    return '{0}_{1}'.format(galaxy_name, galaxy_id)


def sort_data(connection, current_jobs, modulus, remainder):
    """
    Sort the list of jobs
    :param current_jobs:
    :return:
    """
    return_data = {}
    for job_name in current_jobs:
        LOG.info('Checking {0}'.format(job_name))
        index = job_name.index('_area')
        galaxy_name = job_name[0:index]

        index1 = job_name.index('_', index + 5)
        area_number = job_name[index + 5: index1]

        # Get the area
        area = connection.execute(select([AREA]).where(AREA.c.area_id == area_number)).first()

        if modulus is None or int(area[AREA.c.galaxy_id]) % modulus == remainder:
            key = build_key(galaxy_name, area[AREA.c.galaxy_id])
            areas = return_data.get(key)
            if areas is None:
                areas = []
                return_data[key] = areas

            areas.append(area_number)

    return return_data


def finish_processing(galaxy_name, galaxy_id, sorted_data):
    """
    Have we finished processing yet
    :param galaxy_id:
    :param galaxy_name:
    :param sorted_data:
    :return:
    """
    return sorted_data.get(build_key(galaxy_name, galaxy_id)) is None


def processed_data(connection, modulus, remainder):
    """
    Work out which galaxies have been processed

    :param connection:
    :return:
    """
    # Get the work units still being processed
    engine = create_engine(BOINC_DB_LOGIN)
    connection_boinc = engine.connect()
    current_jobs = []
    LOG.info('Getting results from BOINC')
    for result in connection_boinc.execute(select([RESULT]).where(RESULT.c.server_state != 5)):
        current_jobs.append(result[RESULT.c.name])
    connection_boinc.close()
    LOG.info('Got results')

    sorted_data = sort_data(connection, current_jobs, modulus, remainder)
    for key in sorted(sorted_data.iterkeys()):
        LOG.info('{0}: {1} results'.format(key, len(sorted_data[key])))

    # Get the galaxies we know are still processing
    processed = []
    for galaxy in connection.execute(select([GALAXY]).where(GALAXY.c.status_id == COMPUTING)):
        if modulus is None or int(galaxy[GALAXY.c.galaxy_id]) % modulus == remainder:
            if finish_processing(galaxy[GALAXY.c.name], galaxy[GALAXY.c.galaxy_id], sorted_data):
                processed.append(galaxy[GALAXY.c.galaxy_id])
                LOG.info('%d %s has completed', galaxy[GALAXY.c.galaxy_id], galaxy[GALAXY.c.name])

    for galaxy_id in processed:
        connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == galaxy_id).values(status_id=PROCESSED, status_time=datetime.datetime.now()))

    LOG.info('Marked %d galaxies ready for archiving', len(processed))
    LOG.info('%d galaxies are still being processed', len(sorted_data))
