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
The module for the compare images
"""
import logging
from database.database_support_core import GALAXY

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.FileHandler('compare_images.log'))
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

class Galaxy:
    """
    A galaxy
    """
    def __init__(self, galaxy_details):
        self.galaxy_id = galaxy_details[GALAXY.c.galaxy_id]
        self.name = galaxy_details[GALAXY.c.name]
        self.dimension_x = galaxy_details[GALAXY.c.dimension_x]
        self.dimension_y = galaxy_details[GALAXY.c.dimension_y]

class MeanSquareError:
    """
    The Mean Square Error
    """
    def __init__(self):
        self.error = 0.0
        self.match = 0
        self.mismatch = 0

class Values:
    """
    The three values
    """
    def __init__(self):
        self.value = None
        self.median = None
        self.highest_prob_bin = None

class ErrorValues:
    """
    The three values
    """
    def __init__(self):
        self.value = MeanSquareError()
        self.median = MeanSquareError()
        self.highest_prob_bin = MeanSquareError()

class MaxMin:
    """
    The maximum and minimum
    """
    def __init__(self):
        self.max = None
        self.min = None

class MaxMins:
    """
    The three values
    """
    def __init__(self):
        self.value = MaxMin()
        self.median = MaxMin()
        self.highest_prob_bin = MaxMin()

def update(value1, value2, mean_squared_error, max_min):
    """
    Update the values
    """
    # Record the maximum and minimums
    if max_min.max is None:
        max_min.max = max(value1, value2)
        max_min.min = min(value1, value2)
    else:
        max_min.max = max(value1, value2, max_min.max)
        max_min.min = min(value1, value2, max_min.min)

    # Are the values different
    if value1 != value2:
        diff = value1 - value2
        mean_squared_error.error += diff * diff
        mean_squared_error.mismatch += 1
    else:
        mean_squared_error.match += 1


def print_mean_square_error(mean_square_error, pixel_count, max_mins):
    """
    Print the mean square error values
    """
    return '{0:10.2g}, {1:10.2g}, {2:10.2g}, {3:8d}, {4:8d}, {5:10.2g}, {6:10.2g}, {7:10.2g}, {8:8d}, {9:8d}, {10:10.2g}, {11:10.2g}, {12:10.2g}, {13:8d}, {14:8d}'.format(
        mean_square_error.value.error / pixel_count,
        max_mins.value.max,
        max_mins.value.min,
        mean_square_error.value.match,
        mean_square_error.value.mismatch,
        mean_square_error.median.error / pixel_count,
        max_mins.median.max,
        max_mins.median.min,
        mean_square_error.median.match,
        mean_square_error.median.mismatch,
        mean_square_error.highest_prob_bin.error / pixel_count,
        max_mins.highest_prob_bin.max,
        max_mins.highest_prob_bin.min,
        mean_square_error.highest_prob_bin.match,
        mean_square_error.highest_prob_bin.mismatch,
    )

def matches(name1, name2):
    """
    Compare the names of galaxies to see if they match.

    Basically only the the last character is allowed to be different
    >>> matches('2MASXJ22080447+0108060c', '2MASXJ22080447+0108060d')
    True
    >>> matches('2MASXJ22080447+0108060', '2MASXJ22080447+0108060d')
    True
    >>> matches('2MASXJ22080447+0108060c', '2MASXJ22080447+0108060')
    True
    >>> matches('2MASXJ22080447+0108060', '2MASXJ22080447+0108060')
    True
    >>> matches('2MASXJ22080447+0108061c', '2MASXJ22080447+0108060d')
    False
    >>> matches('2MASXJ22080447+0108061', '2MASXJ22080447+0108060d')
    False
    >>> matches('2MASXJ22080447+0108061c', '2MASXJ22080447+0108060')
    False
    >>> matches('2MASXJ22080447+0108061', '2MASXJ22080447+0108060')
    False
    """
    if name1 is None or name2 is None:
        return False

    # Strings ending in a digit should be the same
    if name1[-1:].isdigit() and name2[-1:].isdigit():
        return name1 == name2

    # The last character of one is a digit
    if name1[-1:].isdigit():
        return  name1 == name2[0:-1]

    if name2[-1:].isdigit():
        return  name1[0:-1] == name2

    return name1[0:-1] == name2[0:-1]

def calculate_mean_squared_error(range_mse, galaxy_details, array01, i, j):
    """
    Calculate the Mean squared error between two galaxies and print it
    """
    mean_squared_error = [ErrorValues() for x in range_mse]

    max_min = [MaxMins() for x in range_mse]
    pixel_count = 0
    for x in range(galaxy_details[0].dimension_x):
        for y in range(galaxy_details[0].dimension_y):
            if array01[x][y][0][i].value is not None and array01[x][y][0][j].value is not None:
                pixel_count += 1
            for z in range_mse:
                if array01[x][y][z][i].value is not None and array01[x][y][z][j].value is not None:
                    update(array01[x][y][z][i].value, array01[x][y][z][j].value, mean_squared_error[z].value, max_min[z].value)
                if array01[x][y][z][i].median is not None and array01[x][y][z][j].median is not None:
                    update(array01[x][y][z][i].median, array01[x][y][z][j].median, mean_squared_error[z].median, max_min[z].median)
                if array01[x][y][z][i].highest_prob_bin is not None and array01[x][y][z][j].highest_prob_bin is not None:
                    update(array01[x][y][z][i].highest_prob_bin, array01[x][y][z][j].highest_prob_bin, mean_squared_error[z].highest_prob_bin, max_min[z].highest_prob_bin)



    LOG.info('''
Galaxy, {0}, {1}
Pixel Count, {2}
Parameter,  MSE Value,       Max,         Min,    Match, Mismatch, MSE Median,        Max,        Min,    Match, Mismatch, MSE High P,        Max,        Min,    Match, Mismatch
fmu_sfh  , {3}
fmu_ir   , {4}
mu       , {5}
s_sfr    , {6}
m        , {7}
ldust    , {8}
mdust    , {9}
sfr      , {10}
'''.format(galaxy_details[i].name,                                                 # 00
        galaxy_details[j].name,                                                    # 01
        pixel_count,                                                               # 02
        print_mean_square_error(mean_squared_error[0], pixel_count, max_min[0]),   # 03
        print_mean_square_error(mean_squared_error[1], pixel_count, max_min[1]),   # 04
        print_mean_square_error(mean_squared_error[2], pixel_count, max_min[2]),   # 05
        print_mean_square_error(mean_squared_error[3], pixel_count, max_min[3]),   # 06
        print_mean_square_error(mean_squared_error[4], pixel_count, max_min[4]),   # 07
        print_mean_square_error(mean_squared_error[5], pixel_count, max_min[5]),   # 08
        print_mean_square_error(mean_squared_error[6], pixel_count, max_min[6]),   # 09
        print_mean_square_error(mean_squared_error[7], pixel_count, max_min[7]),   # 10
    ))
