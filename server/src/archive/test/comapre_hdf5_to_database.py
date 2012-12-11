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
Compare the values in the database to those in the HDF5 file
"""

from __future__ import print_function
import logging
import os
import sys

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '../..')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../../boinc/py')))
LOG.info('PYTHONPATH = {0}'.format(sys.path))

import argparse
import h5py
import time
from archive.archive_hdf5_mod import store_fits_header, store_area, store_image_filters, store_area_user, store_pixels
from config import DB_LOGIN
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from database.database_support_core import GALAXY, PIXEL_RESULT, PIXEL_FILTER, FITS_HEADER
from utils.readable_dir import ReadableDir
from sqlalchemy.sql.expression import func, and_

parser = argparse.ArgumentParser('Check a Galaxy by galaxy_id')
parser.add_argument('-o','--output_dir', action=ReadableDir, nargs=1, help='where the HDF5 files have been written')
parser.add_argument('galaxy_id', nargs='+', help='the galaxy_id or 4-30 if you need a range')
args = vars(parser.parse_args())

OUTPUT_DIRECTORY = args['output_dir']
OUTPUT_FORMAT = 'Version 1.00'

# Connect to the two databases
engine_aws = create_engine(DB_LOGIN)
connection = engine_aws.connect()
error_count = 0

def compare(tag, param1, param2):
    """
    Compare two results to make sure they are the same
    """
    global error_count
    if param1 != param2:
        LOG.warning('{0} - {1} != {2}'.format(tag, param1, param2))
        error_count += 1

def check_galaxy_attributes(galaxy):
    """
    Check the galaxy attributes
    """
    compare('galaxy_id'        , galaxy_group.attrs['galaxy_id']        , galaxy[GALAXY.c.galaxy_id]         )
    compare('run_id'           , galaxy_group.attrs['run_id']           , galaxy[GALAXY.c.run_id]            )
    compare('name'             , galaxy_group.attrs['name']             , galaxy[GALAXY.c.name]              )
    compare('dimension_x'      , galaxy_group.attrs['dimension_x']      , galaxy[GALAXY.c.dimension_x]       )
    compare('dimension_y'      , galaxy_group.attrs['dimension_y']      , galaxy[GALAXY.c.dimension_y]       )
    compare('dimension_z'      , galaxy_group.attrs['dimension_z']      , galaxy[GALAXY.c.dimension_z]       )
    compare('redshift'         , galaxy_group.attrs['redshift']         , float(galaxy[GALAXY.c.redshift])   )
    compare('create_time'      , galaxy_group.attrs['create_time']      , str(galaxy[GALAXY.c.create_time])  )
    compare('image_time'       , galaxy_group.attrs['image_time']       , str(galaxy[GALAXY.c.image_time])   )
    compare('version_number'   , galaxy_group.attrs['version_number']   , galaxy[GALAXY.c.version_number]    )
    compare('current'          , galaxy_group.attrs['current']          , galaxy[GALAXY.c.current]           )
    compare('galaxy_type'      , galaxy_group.attrs['galaxy_type']      , galaxy[GALAXY.c.galaxy_type]       )
    compare('ra_cent'          , galaxy_group.attrs['ra_cent']          , galaxy[GALAXY.c.ra_cent]           )
    compare('dec_cent'         , galaxy_group.attrs['dec_cent']         , galaxy[GALAXY.c.dec_cent]          )
    compare('sigma'            , galaxy_group.attrs['sigma']            , float(galaxy[GALAXY.c.sigma])      )
    compare('pixel_count'      , galaxy_group.attrs['pixel_count']      , galaxy[GALAXY.c.pixel_count]       )
    compare('pixels_processed' , galaxy_group.attrs['pixels_processed'] , galaxy[GALAXY.c.pixels_processed]  )
    compare('output_format'    , galaxy_group.attrs['output_format']    , OUTPUT_FORMAT                      )


def compare_fits_header(count, hdf5_data, db_data):
    """
    Compare fits headers
    """
    global error_count
    if db_data[FITS_HEADER.c.keyword] != hdf5_data[0]:
        LOG.warning('Fits Header {0} - Keyword {1} != {2}'.format(count, db_data[FITS_HEADER.c.keyword], hdf5_data[0]))
        error_count += 1

    if db_data[FITS_HEADER.c.value] != hdf5_data[1]:
        LOG.warning('Fits Header {0} - Value {1} != {2}'.format(count, db_data[FITS_HEADER.c.value], hdf5_data[1]))
        error_count += 1

def check_fits_header(galaxy_id, galaxy_group):
    """
    Check the fits header
    """
    data = galaxy_group['fits_header']
    count = 0
    for fits_header in connection.execute(select([FITS_HEADER]).where(FITS_HEADER.c.galaxy_id == galaxy_id)):
        compare_fits_header(count, data[count], fits_header)
        count += 1

try:
    # Get the galaxies to work on
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

        galaxy_id1 = int(galaxy_id_str)
        galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id1)).first()
        if galaxy is None:
            LOG.info('Error: Galaxy with galaxy_id of %d was not found', galaxy_id1)
        else:
            LOG.info('Archiving Galaxy with galaxy_id of %d - %s', galaxy_id1, galaxy[GALAXY.c.name])

            # Copy the galaxy details
            if galaxy[GALAXY.c.version_number] == 1:
                filename = os.path.join(OUTPUT_DIRECTORY, '{0}.hdf5'.format(galaxy[GALAXY.c.name]))
            else:
                filename = os.path.join(OUTPUT_DIRECTORY, '{0}_V{1}.hdf5'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number]))

            h5_file = h5py.File(filename, 'r')

            galaxy_id_aws = galaxy[GALAXY.c.galaxy_id]

            galaxy_group = h5_file['galaxy']
            area_group = galaxy_group['area']
            pixel_group = galaxy_group['pixel']

            check_galaxy_attributes(galaxy)
            check_fits_header(galaxy_id_aws, galaxy_group)

except Exception:
    LOG.exception('Major error')

finally:
    connection.close()

LOG.info('{0} errors found.'.format(error_count))
