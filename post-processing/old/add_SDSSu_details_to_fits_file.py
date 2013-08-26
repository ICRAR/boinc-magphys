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
Is the SDSSu band is missing add it to layer 0
"""
import argparse
import logging
import os
import pyfits

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser()
parser.add_argument('file_names', nargs='+', help='the files to be checked')
args = vars(parser.parse_args())

for file_name in args['file_names']:
    if os.path.isfile(file_name):
        LOG.info('Fixing %s', file_name)

        hdu_list = pyfits.open(file_name, memmap=True)

        hdu_list[0].header.update('MAGPHYSN', 'SDSSu')
        hdu_list[0].header.update('MAGPHYSL', '0.3534')
        hdu_list[0].header.update('MAGPHYSI', '229')
        hdu_list[0].header.update('MAGPHYSF', '1')

        hdu_list.writeto('{0}.fixed.fits'.format(file_name), clobber=True, output_verify='fix')
