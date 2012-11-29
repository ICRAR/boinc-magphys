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
Archive a galaxy and all it's related data. Then delete some elements
"""
from __future__ import print_function
import argparse
import logging
import time
from archive.archive_galaxy_mod import insert_latest, insert_only
from config import DB_LOGIN, PLEIADES_DB_LOGIN
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from database.database_support_core import GALAXY, AREA, PIXEL_RESULT, PIXEL_FILTER, PIXEL_PARAMETER, PIXEL_HISTOGRAM, RUN, RUN_FILE, RUN_FILTER, REGISTER, FITS_HEADER, IMAGE_FILTERS_USED, AREA_USER

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Archive Galaxy by galaxy_id')
parser.add_argument('galaxy_id', nargs='+', help='the galaxy_id or 4-30 if you need a range')
args = vars(parser.parse_args())

# Connect to the two databases
engine_aws = create_engine(DB_LOGIN)
connection_aws = engine_aws.connect()

engine_pleiades = create_engine(PLEIADES_DB_LOGIN)
connection_pleiades = engine_pleiades.connect()

try:
    transaction_pleiades = connection_pleiades.begin()
    # Check the run tables are up to date
    insert_latest(RUN, engine_aws, connection_pleiades)
    insert_latest(RUN_FILE, engine_aws, connection_pleiades)
    insert_latest(RUN_FILTER, engine_aws, connection_pleiades)
    insert_latest(REGISTER, engine_aws, connection_pleiades)

    transaction_pleiades.commit()

    galaxy_ids = None
    if len(args['galaxy_id']) == 1 and args['galaxy_id'][0].find('-') > 1:
        list = args['galaxy_id'][0].split('-')
        LOG.info('Range from %s to %s', list[0], list[1])
        galaxy_ids = range(int(list[0]), int(list[1]) + 1)
    else:
        galaxy_ids = args['galaxy_id']

    for galaxy_id_str in galaxy_ids:
        start_time = time.time()
        area_count = 0
        pixel_count = 0
        transaction_aws = connection_aws.begin()
        transaction_pleiades = connection_pleiades.begin()
        galaxy_id1 = int(galaxy_id_str)
        galaxy_aws = connection_aws.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id1)).first()
        if galaxy_aws is None:
            LOG.info('Error: Galaxy with galaxy_id of %d was not found', galaxy_id1)
        else:
            LOG.info('Archiving Galaxy with galaxy_id of %d - %s', galaxy_id1, galaxy_aws[GALAXY.c.name])

            # Copy the galaxy details
            insert_only(GALAXY, galaxy_aws, connection_pleiades)
            galaxy_id_aws = galaxy_aws[GALAXY.c.galaxy_id]
            for area in connection_aws.execute(select([AREA]).where(AREA.c.galaxy_id == galaxy_id_aws)):
                area_count += 1
                insert_only(AREA, area, connection_pleiades)
                area_id_aws = area[AREA.c.area_id]
                for pixel_result in connection_aws.execute(select([PIXEL_RESULT]).where(PIXEL_RESULT.c.area_id == area_id_aws)):
                    pixel_count += 1
                    pxresult_id_aws = pixel_result[PIXEL_RESULT.c.pxresult_id]
                    insert_only(PIXEL_RESULT, pixel_result, connection_pleiades)

                    for pixel_filter in connection_aws.execute(select([PIXEL_FILTER]).where(PIXEL_FILTER.c.pxresult_id == pxresult_id_aws)):
                        insert_only(PIXEL_FILTER, pixel_filter, connection_pleiades)
                    for pixel_parameter in connection_aws.execute(select([PIXEL_PARAMETER]).where(PIXEL_PARAMETER.c.pxresult_id == pxresult_id_aws)):
                        insert_only(PIXEL_PARAMETER, pixel_parameter, connection_pleiades)
                    for pixel_histogram in connection_aws.execute(select([PIXEL_HISTOGRAM]).where(PIXEL_HISTOGRAM.c.pxresult_id == pxresult_id_aws)):
                        insert_only(PIXEL_HISTOGRAM, pixel_histogram, connection_pleiades)

                for area_user in connection_aws.execute(select([AREA_USER]).where(AREA_USER.c.area_id == area_id_aws)):
                    insert_only(AREA_USER, area_user, connection_pleiades)

                transaction_pleiades.commit()
                transaction_pleiades = connection_aws.begin()

            for fits_header in connection_aws.execute(select([FITS_HEADER]).where(FITS_HEADER.c.galaxy_id == galaxy_id_aws)):
                insert_only(FITS_HEADER, fits_header, connection_pleiades)
            for image_filters_used in connection_aws.execute(select([IMAGE_FILTERS_USED]).where(IMAGE_FILTERS_USED.c.galaxy_id == galaxy_id_aws)):
                insert_only(IMAGE_FILTERS_USED, image_filters_used, connection_pleiades)

            transaction_pleiades.commit()
            copy_end_time = time.time()

            # Now we can delete the bits we don't need
            deleted_area_count = 0
            deleted_pixel_count = 0
            if False:
                for area_id1 in connection_aws.execute(select([AREA.c.area_id]).where(AREA.c.galaxy_id == galaxy_id_aws).order_by(AREA.c.area_id)):
                    deleted_area_count += 1
                    for pxresult_id1 in connection_aws.execute(select([PIXEL_RESULT.c.pxresult_id]).where(PIXEL_RESULT.c.area_id == area_id1[0]).order_by(PIXEL_RESULT.c.pxresult_id)):
                        deleted_pixel_count += 1
                        connection_aws.execute(PIXEL_FILTER.delete().where(PIXEL_FILTER.c.pxresult_id == pxresult_id1[0]))
                        connection_aws.execute(PIXEL_PARAMETER.delete().where(PIXEL_PARAMETER.c.pxresult_id == pxresult_id1[0]))
                        connection_aws.execute(PIXEL_HISTOGRAM.delete().where(PIXEL_HISTOGRAM.c.pxresult_id == pxresult_id1[0]))

                    connection_aws.execute(PIXEL_RESULT.delete().where(PIXEL_RESULT.c.area_id == area_id1[0]))

                    transaction_aws.commit()
                    transaction_aws = connection_aws.begin()

                    # Give the rest of the world a chance to access the database
                    time.sleep(1)

            transaction_aws.commit()
            end_time = time.time()
            LOG.info('Galaxy with galaxy_id of %d was archived.', galaxy_id1)
            LOG.info('Copied %d areas %d pixels.', area_count, pixel_count)
            LOG.info('Deleted %d areas %d pixels.', deleted_area_count, deleted_pixel_count)
            total_time = end_time - start_time
            LOG.info('Total time %d mins %.1f secs', int(total_time / 60), total_time % 60)
            copy_time = copy_end_time - start_time
            LOG.info('Time to copy %d mins %.1f secs', int(copy_time / 60), copy_time % 60)
            delete_time = end_time - copy_end_time
            LOG.info('Time to delete %d mins %.1f secs', int(delete_time / 60), delete_time % 60)

except Exception:
    LOG.exception('Major error')

finally:
    connection_aws.close()
    connection_pleiades.close()
