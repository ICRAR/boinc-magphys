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
from database.database_support_core import GALAXY

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


def update(value1, value2, mean_squared_error):
    if value1 != value2:
        diff = value1 - value2
        mean_squared_error.error += diff * diff
        mean_squared_error.mismatch += 1
    else:
        mean_squared_error.match += 1


def print_mean_square_error(mean_square_error, pixel_count):
    return '{0:10.2g} ({1:5d} {2:5d}) {3:10.2g} ({4:5d} {5:5d}) {6:10.2g} ({7:5d} {8:5d})'.format(mean_square_error.value.error / pixel_count,
        mean_square_error.value.match,
        mean_square_error.value.mismatch,
        mean_square_error.median.error / pixel_count,
        mean_square_error.median.match,
        mean_square_error.median.mismatch,
        mean_square_error.highest_prob_bin.error / pixel_count,
        mean_square_error.highest_prob_bin.match,
        mean_square_error.highest_prob_bin.mismatch,
    )
