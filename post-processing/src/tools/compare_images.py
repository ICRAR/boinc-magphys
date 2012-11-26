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
Compare two images and build a multi-layered fits image of the results
"""
from __future__ import print_function
import argparse
import logging
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import and_
from config import DB_LOGIN
from database.database_support_core import GALAXY, PIXEL_RESULT, PIXEL_PARAMETER
from tools.compare_images_mod import Galaxy, Values, matches, calculate_mean_squared_error
from tools.compare_images_plot import plot_differences

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.FileHandler('compare_images.log'))
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Compare a number of galaxies')
parser.add_argument('calc', choices=['mse', 'hist'], help='are we calculating mse or plotting differences')
parser.add_argument('type', choices=['run', 'galaxy'], help='are the ids galaxy or run ids')
parser.add_argument('ids', nargs='*', type=int, help='the galaxy_ids of the galaxies to compare or the run_ids')
args = vars(parser.parse_args())

IMAGE_NAMES = ['fmu_sfh', 'fmu_ir', 'mu', 's_sfr', 'm', 'ldust', 'mdust', 'sfr']
LEN_NAMES = len(IMAGE_NAMES)
PARAMETER_NUMBERS = [1, 2, 3, 5, 6, 7, 15, 16]

# First check the galaxy exists in the database
engine = create_engine(DB_LOGIN)
connection = engine.connect()

if args['type'] == 'galaxy':
    # If we are looking just at galaxy ids pass them through
    list_galaxy_ids = [args['ids']]
else:
    # Build the galaxy ids from the run ids
    list_galaxy_ids = []
    name = None
    galaxy_ids = []
    for galaxy_details in connection.execute(select([GALAXY.c.name, GALAXY.c.galaxy_id]).where(GALAXY.c.run_id.in_(args['ids'])).order_by(GALAXY.c.name)):
        if matches(name, galaxy_details[0]):
            galaxy_ids.append(galaxy_details[1])
        else:
            name = galaxy_details[0]
            galaxy_ids = [galaxy_details[1]]
            list_galaxy_ids.append(galaxy_ids)

for galaxy_ids in list_galaxy_ids:
    galaxy_details = []
    for galaxy in connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id.in_(galaxy_ids))):
        galaxy_details.append(Galaxy(galaxy))

    if len(galaxy_details) < 2:
        LOG.error('%d galaxies found', len(galaxy_details))
        break

    len_galaxy_ids = len(galaxy_details)
    for i in range(len_galaxy_ids - 1):
        if galaxy_details[i].dimension_x != galaxy_details[i + 1].dimension_x or galaxy_details[i].dimension_y != galaxy_details[i + 1].dimension_y:
            LOG.error('The galaxies are different sizes (%d x %d) vs (%d x %d)', galaxy_details[i].dimension_x, galaxy_details[i].dimension_y, galaxy_details[i + 1].dimension_x, galaxy_details[i + 1].dimension_y)
            exit(1)

    array01 = [[[[Values() for galaxies in range(len(galaxy_details))] for depth in range(LEN_NAMES)] for col in range(galaxy_details[0].dimension_y)] for row in range(galaxy_details[0].dimension_x)]

    # Load the data
    for i in range(len(galaxy_details)):
        LOG.info('Loading %s', galaxy_details[i].name)
        for pixel in connection.execute(select([PIXEL_RESULT]).where(PIXEL_RESULT.c.galaxy_id == galaxy_details[i].galaxy_id)):
            array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][0][i].value = pixel[PIXEL_RESULT.c.fmu_sfh]
            array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][1][i].value = pixel[PIXEL_RESULT.c.fmu_ir]
            array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][2][i].value = pixel[PIXEL_RESULT.c.mu]
            array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][3][i].value = pixel[PIXEL_RESULT.c.s_sfr]
            array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][4][i].value = pixel[PIXEL_RESULT.c.m]
            array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][5][i].value = pixel[PIXEL_RESULT.c.ldust]
            array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][6][i].value = pixel[PIXEL_RESULT.c.mdust]
            array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][7][i].value = pixel[PIXEL_RESULT.c.sfr]

            j = 0
            for pixel_parameter in connection.execute(select([PIXEL_PARAMETER])
                    .where(and_(PIXEL_PARAMETER.c.pxresult_id == pixel[PIXEL_RESULT.c.pxresult_id], PIXEL_PARAMETER.c.parameter_name_id.in_(PARAMETER_NUMBERS)))
                    .order_by(PIXEL_PARAMETER.c.parameter_name_id)):
                array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][j][i].median           = pixel_parameter[PIXEL_PARAMETER.c.percentile50]
                array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][j][i].highest_prob_bin = pixel_parameter[PIXEL_PARAMETER.c.high_prob_bin]
                j += 1

    # Now compare them all
    LOG.info('Comparing them all')
    for i in range(len_galaxy_ids - 1):
        for j in range(i + 1, len_galaxy_ids):
            if args['calc'] == 'mse':
                calculate_mean_squared_error(range(LEN_NAMES), galaxy_details, array01, i, j)
            else:
                plot_differences(IMAGE_NAMES, galaxy_details, array01, i, j)
