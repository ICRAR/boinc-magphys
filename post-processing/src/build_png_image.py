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
Build a PNG image from the data in the database
"""
import os
import sys
import logging

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '../../server/src')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../boinc/py')))
LOG.info('PYTHONPATH = {0}'.format(sys.path))

import argparse
import math
import numpy
import datetime
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import and_
from config import DB_LOGIN
from config import DJANGO_IMAGE_DIR
from image import fitsimage, directory_mod
from database.database_support_core import AREA, GALAXY, PIXEL_RESULT, PIXEL_PARAMETER
from PIL import Image

parser = argparse.ArgumentParser('Build images from the POGS results')
parser.add_argument('names', nargs='*', help='optional the name of the galaxies to produce')
parser.add_argument('-all', action='store_true', help='build images for all the galaxies')
args = vars(parser.parse_args())

output_directory = DJANGO_IMAGE_DIR

# First check the galaxy exists in the database
engine = create_engine(DB_LOGIN)
connection = engine.connect()

query = select([GALAXY]).distinct()
if len(args['names']) > 0:
    LOG.info('Building PNG files for the galaxies {0}'.format(args['names']))
    query = query.where(GALAXY.c.name.in_(args['names']))
elif args['all']:
    LOG.info('Building PNG files for all the galaxies')
    query = query.order_by(GALAXY.c.name)
else:
    LOG.info('Building PNG files for updated galaxies')
    query = query.where(and_(AREA.c.galaxy_id == GALAXY.c.galaxy_id, AREA.c.update_time >= GALAXY.c.image_time))

IMAGE_NAMES = [ 'fmu_sfh',
                'fmu_ir',
                'mu',
                'tauv',
                's_sfr',
                'm',
                'ldust',
                't_w_bc',
                't_c_ism',
                'xi_c_tot',
                'xi_pah_tot',
                'xi_mir_tot',
                'x_w_tot',
                'tvism',
                'mdust',
                'sfr',
              ]

PNG_IMAGE_NAMES = [ 'mu',
                    'm',
                    'ldust',
                    'sfr',
              ]

# 'Fire' (Copied from Aladin cds.aladin.ColorMap.java)
FIRE_R = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,4,7,
       10,13,16,19,22,25,28,31,34,37,40,43,46,49,52,55,58,61,64,67,70,73,76,79,
       82,85,88,91,94,98,101,104,107,110,113,116,119,122,125,128,131,134,137,
       140,143,146,148,150,152,154,156,158,160,162,163,164,166,167,168,170,171,
       173,174,175,177,178,179,181,182,184,185,186,188,189,190,192,193,195,196,
       198,199,201,202,204,205,207,208,209,210,212,213,214,215,217,218,220,221,
       223,224,226,227,229,230,231,233,234,235,237,238,240,241,243,244,246,247,
       249,250,252,252,252,253,253,253,254,254,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255]

FIRE_G = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,1,3,5,7,8,10,12,14,16,19,21,24,27,29,32,35,37,40,43,46,48,
       51,54,57,59,62,65,68,70,73,76,79,81,84,87,90,92,95,98,101,103,105,107,
       109,111,113,115,117,119,121,123,125,127,129,131,133,134,136,138,140,141,
       143,145,147,148,150,152,154,155,157,159,161,162,164,166,168,169,171,173,
       175,176,178,180,182,184,186,188,190,191,193,195,197,199,201,203,205,206,
       208,210,212,213,215,217,219,220,222,224,226,228,230,232,234,235,237,239,
       241,242,244,246,248,248,249,250,251,252,253,254,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
       255,255,255,255,255,255,255,255]

FIRE_B = [0,7,15,22,30,38,45,53,61,65,69,74,78,
       82,87,91,96,100,104,108,113,117,121,125,130,134,138,143,147,151,156,160,
       165,168,171,175,178,181,185,188,192,195,199,202,206,209,213,216,220,220,
       221,222,223,224,225,226,227,224,222,220,218,216,214,212,210,206,202,199,
       195,191,188,184,181,177,173,169,166,162,158,154,151,147,143,140,136,132,
       129,125,122,118,114,111,107,103,100,96,93,89,85,82,78,74,71,67,64,60,56,
       53,49,45,42,38,35,31,27,23,20,16,12,8,5,4,3,3,2,1,1,0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
       4,8,13,17,21,26,30,35,42,50,58,66,74,82,90,98,105,113,121,129,136,144,
       152,160,167,175,183,191,199,207,215,223,227,231,235,239,243,247,251,255,
       255,255,255,255,255,255,255]

fits_image = fitsimage.FitsImage(connection)
galaxy_count = 0
for galaxy in connection.execute(query):
    LOG.info('Working on galaxy %s', galaxy[GALAXY.c.name])
    array = numpy.empty((galaxy[GALAXY.c.dimension_y], galaxy[GALAXY.c.dimension_x], len(PNG_IMAGE_NAMES)), dtype=numpy.float)
    array.fill(numpy.NaN)

    # Return the rows
    pixel_count = 0
    pixels_processed = 0
    for row in connection.execute(select([PIXEL_RESULT]).where(PIXEL_RESULT.c.galaxy_id == galaxy[GALAXY.c.galaxy_id])):
        row__x = row[PIXEL_RESULT.c.x]
        row__y = row[PIXEL_RESULT.c.y]
        pixel_count += 1
        if row[PIXEL_RESULT.c.workunit_id] is not None:
            pixels_processed += 1

        # Now get the median values
        for pixel_parameter in connection.execute(select([PIXEL_PARAMETER]).
                where(and_(PIXEL_PARAMETER.c.pxresult_id == row[PIXEL_RESULT.c.pxresult_id], PIXEL_PARAMETER.c.parameter_name_id.in_([3,6,7,16])))):
            if pixel_parameter[PIXEL_PARAMETER.c.parameter_name_id] == 3:
                array[row__y, row__x, 0] = pixel_parameter[PIXEL_PARAMETER.c.percentile50]
            elif pixel_parameter[PIXEL_PARAMETER.c.parameter_name_id] == 6:
                array[row__y, row__x, 1] = pixel_parameter[PIXEL_PARAMETER.c.percentile50]
            elif pixel_parameter[PIXEL_PARAMETER.c.parameter_name_id] == 7:
                array[row__y, row__x, 2] = pixel_parameter[PIXEL_PARAMETER.c.percentile50]
            elif pixel_parameter[PIXEL_PARAMETER.c.parameter_name_id] == 16:
                # the SFR is a log
                array[row__y, row__x, 3] = math.pow(10, pixel_parameter[PIXEL_PARAMETER.c.percentile50])

    name_count = 0

    transaction = connection.begin()
    connection.execute(GALAXY.update().
        where(GALAXY.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]).
        values(image_time = datetime.datetime.now(), pixel_count = pixel_count, pixels_processed = pixels_processed))
    transaction.commit()
    galaxy_count += 1

    # Now right the files
    blackRGB = (0, 0, 0)
    for name in PNG_IMAGE_NAMES:
        value = 0
        height = galaxy[GALAXY.c.dimension_y]
        width  = galaxy[GALAXY.c.dimension_x]
        idx = 0
        if name == 'mu':
            idx = 0
        elif name == 'm':
            idx = 1
        elif name == 'ldust':
            idx = 2
        elif name == 'sfr':
            idx = 3

        values = []
        for x in range(0, width-1):
            for y in range(0, height-1):
                value =  array[y, x, idx]
                if not math.isnan(value) and value > 0:
                    values.append(value)

        values.sort()
        if len(values) > 1000:
            top_count = int(len(values)*0.005)
            top_value = values[len(values)-top_count]
        elif len(values) > 0:
            top_value = values[len(values)-1]
        else:
            top_value = 1
        if len(values) > 1:
            median_value = values[int(len(values)/2)]
        elif len(values) > 0:
            median_value = values[0]
        else:
            median_value = 1

        sigma = 1 / median_value
        multiplier = 255.0 / math.asinh(top_value * sigma)

        image = Image.new("RGB", (width, height), blackRGB)
        for x in range(0, width-1):
            for y in range(0, height-1):
                value = array[y, x, idx]
                if not math.isnan(value) and value > 0:
                    value = int(math.asinh(value * sigma) * multiplier)
                    if value > 255:
                        value = 255
                    red = FIRE_R[value]
                    green = FIRE_G[value]
                    blue = FIRE_B[value]
                    image.putpixel((x, height-y-1), (red, green, blue))
        out_name = directory_mod.get_file_path(output_directory, '{0}_{1}_{2}.png'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number], name), True)
        image.save(out_name)

LOG.info('Built images for %d galaxies', galaxy_count)

