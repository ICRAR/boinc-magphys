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
Initialise the Constants used
"""

import re

HEADER_PATTERNS = [re.compile('CDELT[0-9]+'),
                   re.compile('CROTA[0-9]+'),
                   re.compile('CRPIX[0-9]+'),
                   re.compile('CRVAL[0-9]+'),
                   re.compile('CTYPE[0-9]+'),
                   re.compile('EQUINOX'),
                   re.compile('EPOCH'),
                   re.compile('RA_CENT'),
                   re.compile('DEC_CENT'),
                   ]

STAR_FORMATION_FILE = 1
INFRARED_FILE       = 2
FILTERS_FILE        = 3
