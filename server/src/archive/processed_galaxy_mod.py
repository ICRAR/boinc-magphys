#
#    Copyright (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
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
from sqlalchemy import select, func, and_
from database.database_support_core import AREA, GALAXY
from sqlalchemy.engine import create_engine
from config import BOINC_DB_LOGIN, PROCESSED, COMPUTING
from database.boinc_database_support_core import RESULT
from utils.logging_helper import config_logger

from utils.shutdown_detection import shutdown

LOG = config_logger(__name__)


class CacheGalaxy:
    def __init__(self, galaxy_name, galaxy_id, area_min, area_max, ignore):
        self.galaxy_name = galaxy_name
        self.galaxy_id = galaxy_id
        self.area_min = area_min
        self.area_max = area_max
        self.ignore = ignore

    def __str__(self):
        return '{0}, {1}, {2}, {3}, {4}'.format(self.galaxy_name, self.galaxy_id, self.area_min, self.area_max, self.ignore)


def build_key(galaxy_name, galaxy_id):
    return '{0}_{1}'.format(galaxy_name, galaxy_id)


def get_cached_galaxy(cache_data, galaxy_name, area_number):
    """
    Get any cached data for this name
    :param cache_data:
    :param galaxy_name:
    :param area_number:
    :return:
    """
    cache_galaxies = cache_data.get(galaxy_name)
    if cache_galaxies is not None:
        for cached_galaxy in cache_galaxies:
            if cached_galaxy.area_min <= area_number <= cached_galaxy.area_max:
                return cached_galaxy

    return None


def sort_data(connection, current_jobs, modulus, remainder):
    """
    Sort the list of jobs

    :param current_jobs:
    :return:
    """
    cache_data = {}
    return_data = {}
    for job_name in current_jobs:
        #LOG.info('Checking {0}'.format(job_name))
        index = job_name.index('_area')
        galaxy_name = job_name[0:index]

        index1 = job_name.index('_', index + 5)
        area_number = job_name[index + 5: index1]

        cached_galaxy = get_cached_galaxy(cache_data, galaxy_name, int(area_number))
        #LOG.info('Cache check = {0}'.format(cached_galaxy))

        if cached_galaxy is None:
            # Get the area
            LOG.info('Area Number = {0}'.format(area_number))
            area = connection.execute(select([AREA]).where(AREA.c.area_id == area_number)).first()
            if area is None:
                LOG.info('Area with id={0} does not exist (Job: {1})'.format(area_number, job_name))
                continue
            ignore = True
            galaxy_id = int(area[AREA.c.galaxy_id])
            if modulus is None or galaxy_id % modulus == remainder:
                ignore = False
                key = build_key(galaxy_name, galaxy_id)
                areas = return_data.get(key)
                if areas is None:
                    areas = []
                    return_data[key] = areas

                areas.append(area_number)

            # Add this galaxy to the cache
            min_max = connection.execute(select([func.min(AREA.c.area_id), func.max(AREA.c.area_id)]).where(AREA.c.galaxy_id == galaxy_id)).first()
            # LOG.info('Adding to cache = {0} {1} {2}'.format(galaxy_name, min_max, ignore))
            list_galaxies = cache_data.get(galaxy_name)
            if list_galaxies is None:
                list_galaxies = []
                cache_data[galaxy_name] = list_galaxies

            list_galaxies.append(CacheGalaxy(galaxy_name, galaxy_id, min_max[0], min_max[1], ignore))

        else:
            if not cached_galaxy.ignore:
                key = build_key(galaxy_name, cached_galaxy.galaxy_id)
                areas = return_data.get(key)
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
    # The use of appid ensures MySQL uses an index otherwise it does a full table scan
    for result in connection_boinc.execute(select([RESULT]).where(and_(RESULT.c.server_state != 5, RESULT.c.appid == 1))):
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

        if shutdown() is True:
            raise SystemExit

    LOG.info('Marked %d galaxies ready for archiving', len(processed))
    LOG.info('%d galaxies are still being processed', len(sorted_data))
