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
import math
import numpy
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import select
from config import DB_LOGIN
from database.database_support_core import GALAXY, PIXEL_RESULT
from utils.writeable_dir import WriteableDir

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Build images by comparing two galaxies')
parser.add_argument('-o','--output_dir', action=WriteableDir, nargs=1, help='where the image will be written')
parser.add_argument('galaxy_id', nargs='*', type=int, help='the galaxy_ids of the galaxies to compare')
args = vars(parser.parse_args())

OUTPUT_DIRECTORY = args['output_dir']
IMAGE_NAMES_AE = ['i_sfh', 'i_ir']
IMAGE_NAMES_MSE = ['fmu_sfh', 'fmu_ir', 'mu', 's_sfr', 'm', 'ldust', 'mdust', 'sfr']

# First check the galaxy exists in the database
engine = create_engine(DB_LOGIN)
connection = engine.connect()

class Galaxy:
    """
    A galaxy
    """
    def __init__(self, galaxy_details):
        self.galaxy_id = galaxy_details[GALAXY.c.galaxy_id]
        self.name = galaxy_details[GALAXY.c.name]
        self.dimension_x = galaxy_details[GALAXY.c.dimension_x]
        self.dimension_y = galaxy_details[GALAXY.c.dimension_y]

galaxy_details = []
for galaxy in connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id.in_(args['galaxy_id']))):
    galaxy_details.append(Galaxy(galaxy))

if len(galaxy_details) != 2:
    LOG.error('%d galaxies found', len(galaxy_details))
    exit(1)

if galaxy_details[0].dimension_x != galaxy_details[1].dimension_x or galaxy_details[0].dimension_y != galaxy_details[1].dimension_y:
    LOG.error('The galaxies are different sizes (%d x %d) vs (%d x %d)', galaxy_details[0].dimension_x, galaxy_details[0].dimension_y, galaxy_details[1].dimension_x, galaxy_details[1].dimension_y)
    exit(1)

array01 = [[[[None, None] for depth in range(len(IMAGE_NAMES_AE) + len(IMAGE_NAMES_MSE))] for col in range(galaxy_details[0].dimension_y)] for row in range(galaxy_details[0].dimension_x)]

# Load the data
for i in range(2):
    for pixel in connection.execute(select([PIXEL_RESULT]).where(PIXEL_RESULT.c.galaxy_id == galaxy_details[i].galaxy_id)):
        array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][0][i] = pixel[PIXEL_RESULT.c.i_sfh]
        array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][1][i] = pixel[PIXEL_RESULT.c.i_ir]
        array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][2][i] = pixel[PIXEL_RESULT.c.fmu_sfh]
        array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][3][i] = pixel[PIXEL_RESULT.c.fmu_ir]
        array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][4][i] = pixel[PIXEL_RESULT.c.mu]
        array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][5][i] = pixel[PIXEL_RESULT.c.s_sfr]
        array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][6][i] = pixel[PIXEL_RESULT.c.m]
        array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][7][i] = pixel[PIXEL_RESULT.c.ldust]
        array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][8][i] = pixel[PIXEL_RESULT.c.mdust]
        array01[pixel[PIXEL_RESULT.c.x]][pixel[PIXEL_RESULT.c.y]][9][i] = pixel[PIXEL_RESULT.c.sfr]

array02 = numpy.empty((galaxy_details[0].dimension_y, galaxy_details[0].dimension_x, len(IMAGE_NAMES_AE) + len(IMAGE_NAMES_MSE)), dtype=numpy.float)

absolute_error = [0 for x in range(len(IMAGE_NAMES_AE))]
mean_squared_error = [0.0 for x in range(len(IMAGE_NAMES_MSE))]

pixel_count = 0
for x in range(galaxy_details[0].dimension_x):
    for y in range(galaxy_details[0].dimension_y):
        if array01[x][y][0][0] is not None and array01[x][y][0][1] is not None:
            pixel_count += 1
        for z in range(len(IMAGE_NAMES_AE)):
            if array01[x][y][z][0] is not None and array01[x][y][z][1] is not None:
                if array01[x][y][z][0] != array01[x][y][z][1]:
                    absolute_error[z] += 1
        for z in range(len(IMAGE_NAMES_AE), len(IMAGE_NAMES_AE) + len(IMAGE_NAMES_MSE)):
            if array01[x][y][z][0] is not None and array01[x][y][z][1] is not None:
                if array01[x][y][z][0] != array01[x][y][z][1]:
                     mean_squared_error[z - len(IMAGE_NAMES_AE)] += math.pow(array01[x][y][z][0] - array01[x][y][z][1], 2)

LOG.info('''
Galaxy {0} vs {1}
Different i_sfh = {2} i_ir = {3}
Pixel Count = {4}

Absolute Error
i_sfh = {5:.2f}% i_ir = {6:.2f}%

Mean Squared Error
fmu_sfh = {7:.2f} fmu_ir = {8:.2f} mu = {9:.2f} s_sfr = {10:.2f} m = {11:.2f} ldust = {12:.2f} mdust = {13:.2f} sfr = {14:.2f}
'''.format(galaxy_details[0].name,
    galaxy_details[1].name,
    absolute_error[0],
    absolute_error[1],
    pixel_count,
    absolute_error[0] * 100.0 / pixel_count,
    absolute_error[1] * 100.0 / pixel_count,
    mean_squared_error[0] / pixel_count,
    mean_squared_error[1] / pixel_count,
    mean_squared_error[2] / pixel_count,
    mean_squared_error[3] / pixel_count,
    mean_squared_error[4] / pixel_count,
    mean_squared_error[5] / pixel_count,
    mean_squared_error[6] / pixel_count,
    mean_squared_error[7] / pixel_count))
