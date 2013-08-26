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
During the Beta testing we stored all the Pixel Parameter values - this script removes the really small values
"""
import argparse
import logging
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import and_
from config import DB_LOGIN, MIN_HIST_VALUE
from database.database_support_core import GALAXY, PIXEL_RESULT, PIXEL_HISTOGRAM

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Delete Galaxy by galaxy_id')
parser.add_argument('galaxy_id', nargs='+', help='the galaxy_id or 4-30 if you need a range')
args = vars(parser.parse_args())

ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()

galaxy_ids = None
deleted_total = 0
if len(args['galaxy_id']) == 1 and args['galaxy_id'][0].find('-') > 1:
    list = args['galaxy_id'][0].split('-')
    LOG.info('Range from %s to %s', list[0], list[1])
    galaxy_ids = range(int(list[0]), int(list[1]) + 1)
else:
    galaxy_ids = args['galaxy_id']

for galaxy_id_str in galaxy_ids:
    galaxy_id1 = int(galaxy_id_str)
    galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id1)).first()
    if galaxy is None:
        LOG.info('Error: Galaxy with galaxy_id of %d was not found', galaxy_id1)
    else:
        # Have we got work units out there for this galaxy?
        LOG.info('Working on galaxy %s (%d)', galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number])

        deleted_galaxy = 0
        transaction = connection.begin()
        count = 0
        for pxresult_id in connection.execute(select([PIXEL_RESULT.c.pxresult_id]).where(PIXEL_RESULT.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]).order_by(PIXEL_RESULT.c.pxresult_id)):
            if not (count % 1000):
                LOG.info('Deleting low pixel_histogram values from galaxy {0} pixel {1} : Deleted total {2} galaxy {3}'.format(galaxy[GALAXY.c.galaxy_id], pxresult_id[0], deleted_total, deleted_galaxy))
            result_proxy = connection.execute(PIXEL_HISTOGRAM.delete().where(and_(PIXEL_HISTOGRAM.c.pxresult_id == pxresult_id[0], PIXEL_HISTOGRAM.c.hist_value < MIN_HIST_VALUE)))
            deleted_total += result_proxy.rowcount
            deleted_galaxy += result_proxy.rowcount
            count += 1

        transaction.commit()
        LOG.info('Removed %d really small histogram values from %s (%d)', deleted_galaxy, galaxy.name, galaxy.version_number)

connection.close()
LOG.info('Done - removed %d really small histogram values.', deleted_total)
