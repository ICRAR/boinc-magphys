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
Archive a galaxy and all it's related data to an HDF5 file. Then delete some elements
"""
from __future__ import print_function
import logging
import os
import sys
from sqlalchemy.sql.expression import func, and_

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../boinc/py')))
LOG.info('PYTHONPATH = {0}'.format(sys.path))

import argparse
import h5py
import time
from archive.archive_hdf5_mod import store_fits_header, store_area, store_image_filters, store_area_user, store_pixels
from config import DB_LOGIN
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from database.database_support_core import GALAXY, PIXEL_RESULT, PIXEL_FILTER
from utils.writeable_dir import WriteableDir

parser = argparse.ArgumentParser('Archive Galaxy by galaxy_id')
parser.add_argument('-o','--output_dir', action=WriteableDir, nargs=1, help='where the HDF5 files will be written')
parser.add_argument('galaxy_id', nargs='+', help='the galaxy_id or 4-30 if you need a range')
args = vars(parser.parse_args())

OUTPUT_DIRECTORY = args['output_dir']
OUTPUT_FORMAT = 'Version 1.00'

# Connect to the two databases
engine_aws = create_engine(DB_LOGIN)
connection = engine_aws.connect()

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

            h5_file = h5py.File(filename, 'w')

            # Build the groups
            galaxy_group = h5_file.create_group('galaxy')
            area_group = galaxy_group.create_group('area')
            pixel_group = galaxy_group.create_group('pixel')

            # Write the galaxy data
            galaxy_group.attrs['galaxy_id']        = galaxy[GALAXY.c.galaxy_id]
            galaxy_group.attrs['run_id']           = galaxy[GALAXY.c.run_id]
            galaxy_group.attrs['name']             = galaxy[GALAXY.c.name]
            galaxy_group.attrs['dimension_x']      = galaxy[GALAXY.c.dimension_x]
            galaxy_group.attrs['dimension_y']      = galaxy[GALAXY.c.dimension_y]
            galaxy_group.attrs['dimension_z']      = galaxy[GALAXY.c.dimension_z]
            galaxy_group.attrs['redshift']         = float(galaxy[GALAXY.c.redshift])
            galaxy_group.attrs['create_time']      = str(galaxy[GALAXY.c.create_time])
            galaxy_group.attrs['image_time']       = str(galaxy[GALAXY.c.image_time])
            galaxy_group.attrs['version_number']   = galaxy[GALAXY.c.version_number]
            galaxy_group.attrs['current']          = galaxy[GALAXY.c.current]
            galaxy_group.attrs['galaxy_type']      = galaxy[GALAXY.c.galaxy_type]
            galaxy_group.attrs['ra_cent']          = galaxy[GALAXY.c.ra_cent]
            galaxy_group.attrs['dec_cent']         = galaxy[GALAXY.c.dec_cent]
            galaxy_group.attrs['sigma']            = float(galaxy[GALAXY.c.sigma])
            galaxy_group.attrs['pixel_count']      = galaxy[GALAXY.c.pixel_count]
            galaxy_group.attrs['pixels_processed'] = galaxy[GALAXY.c.pixels_processed]
            galaxy_group.attrs['output_format']    = OUTPUT_FORMAT

            galaxy_id_aws = galaxy[GALAXY.c.galaxy_id]

            # Store the data associated with the galaxy
            store_fits_header(connection, galaxy_id_aws, galaxy_group)
            store_image_filters(connection, galaxy_id_aws, galaxy_group)

            # Store the data associated with the areas
            area_count = store_area(connection, galaxy_id_aws, area_group)
            store_area_user(connection, galaxy_id_aws, area_group)
            h5_file.flush()

            # How many filter layers are there (check a row with some)
            pixel_result = connection.execute(select([PIXEL_RESULT]).where(and_(PIXEL_RESULT.c.galaxy_id == galaxy_id1, PIXEL_RESULT.c.i_sfh != None))).first()
            filter_layers = connection.execute(select([func.count(PIXEL_FILTER.c.pxfilter_id)]).where(PIXEL_FILTER.c.pxresult_id == pixel_result[PIXEL_RESULT.c.pxresult_id])).first()[0]

            # Store the values associated with a pixel
            pixel_count = store_pixels(connection,
                galaxy_id_aws,
                pixel_group,
                galaxy[GALAXY.c.dimension_x],
                galaxy[GALAXY.c.dimension_y],
                filter_layers,
                galaxy[GALAXY.c.pixel_count])

            # Flush the HDF5 data to disk
            h5_file.flush()
            h5_file.close()
            end_time = time.time()
            LOG.info('Galaxy with galaxy_id of %d was archived.', galaxy_id1)
            LOG.info('Copied %d areas %d pixels.', area_count, pixel_count)
            total_time = end_time - start_time
            LOG.info('Total time %d mins %.1f secs', int(total_time / 60), total_time % 60)

except Exception:
    LOG.exception('Major error')

finally:
    connection.close()
