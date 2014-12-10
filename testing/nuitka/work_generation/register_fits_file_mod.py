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
Functions used my register
"""
from decimal import Decimal
from utils.logging_helper import config_logger

LOG = config_logger(__name__)
FOUR_PLACES = Decimal('.0001')
FIVE_PLACES = Decimal('.00001')


def fix_redshift(redshift_in):
    """
    Fix the redshift if it happens to be exactly on the boundary between two models.

    0.005, 0.015 - need to be nudged down to make sure they work proper


    >>> fix_redshift('0.00')
    Decimal('0.00000')

    >>> fix_redshift('0.005')
    Decimal('0.00490')
    """
    redshift = Decimal(redshift_in).quantize(FIVE_PLACES)
    if str(redshift)[-3:] == '500':
        redshift -= FOUR_PLACES

    return redshift
