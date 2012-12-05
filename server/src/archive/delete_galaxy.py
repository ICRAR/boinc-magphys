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
from __future__ import print_function
import argparse
import logging
import sys
import time
from config import DB_LOGIN
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from database.database_support_core import GALAXY, AREA, PIXEL_RESULT, PIXEL_FILTER, PIXEL_PARAMETER, PIXEL_HISTOGRAM, AREA_USER, FITS_HEADER

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Delete Galaxy by galaxy_id')
parser.add_argument('galaxy_id', nargs='+', help='the galaxy_id or 4-30 if you need a range')
args = vars(parser.parse_args())

# First check the galaxy exists in the database
ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()

galaxy_ids = None
if len(args['galaxy_id']) == 1 and args['galaxy_id'][0].find('-') > 1:
    list = args['galaxy_id'][0].split('-')
    LOG.info('Range from %s to %s', list[0], list[1])
    galaxy_ids = range(int(list[0]), int(list[1]) + 1)
else:
    galaxy_ids = args['galaxy_id']

for galaxy_id_str in galaxy_ids:
    transaction = connection.begin()
    galaxy_id1 = int(galaxy_id_str)
    galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id1)).first()
    if galaxy is None:
        LOG.info('Error: Galaxy with galaxy_id of %d was not found', galaxy_id1)
    else:
        LOG.info('Deleting Galaxy with galaxy_id of %d - %s', galaxy_id1, galaxy[GALAXY.x.name])

        for area_id1 in connection.execute(select([AREA.c.area_id]).where(AREA.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]).order_by(AREA.c.area_id)):
            for pxresult_id1 in connection.execute(select([PIXEL_RESULT.c.pxresult_id]).where(PIXEL_RESULT.c.area_id == area_id1[0]).order_by(PIXEL_RESULT.c.pxresult_id)):
                print("Deleting galaxy {0} area {1} pixel {2}".format(galaxy_id_str, area_id1[0], pxresult_id1[0]), end="\r")
                sys.stdout.flush()

                connection.execute(PIXEL_FILTER.delete().where(PIXEL_FILTER.cpxresult_id == pxresult_id1[0]))
                connection.execute(PIXEL_PARAMETER.delete().where(PIXEL_PARAMETER.c.pxresult_id == pxresult_id1[0]))
                connection.execute(PIXEL_HISTOGRAM.delete().where(PIXEL_HISTOGRAM.c.pxresult_id == pxresult_id1[0]))

            connection.execute(PIXEL_RESULT.delete().where(PIXEL_RESULT.c.area_id == area_id1[0]))
            connection.execute(AREA_USER.delete().where(AREA_USER.c.area_id == area_id1[0]))

            transaction.commit()
            transaction = connection.begin()

            # Give the rest of the world a chance to access the database
            time.sleep(10)

        connection.execute(AREA.delete().where(AREA.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]))
        connection.execute(FITS_HEADER.delete().where(FITS_HEADER.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]))
        connection.execute(GALAXY.delete().where(GALAXY.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]))

        #TODO Remove the images
        LOG.info('Galaxy with galaxy_id of %d was deleted', galaxy_id1)
    transaction.commit()

connection.close()
