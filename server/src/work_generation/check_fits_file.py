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
Check the characteristics of the fits file
"""
import argparse
import glob
from utils.logging_helper import config_logger
import os
import pyfits

LOG = config_logger(__name__)
LOG.info('PYTHONPATH = {0}'.format(sys.path))

parser = argparse.ArgumentParser()
parser.add_argument('file_names', nargs='+', help='the files to be checked')
args = vars(parser.parse_args())

for file_name_stub in args['file_names']:
    for file_name in glob.glob(file_name_stub):
        if os.path.isfile(file_name):
            LOG.info('Check %s', file_name)

            hdu_list = pyfits.open(file_name, memmap=True)
            layer_count = len(hdu_list)

            end_y = hdu_list[0].data.shape[0]
            end_x = hdu_list[0].data.shape[1]

            LOG.info("Image dimensions: %(x)d x %(y)d x %(z)d => %(pix).2f Mpixels" % {'x': end_x,'y': end_y,'z': layer_count,'pix': end_x * end_y/1000000.0})

            # Read the fits headers
            for layer in range(layer_count):
                header = hdu_list[layer].header
                for keyword in header:
                    if header.comments[keyword] is None:
                        LOG.info('** Layer %d - %s: %s', layer, keyword, header[keyword])
                    else:
                        LOG.info('** Layer %d - %s: %s: %s', layer, keyword, header[keyword], header.comments[keyword])
        else:
            LOG.info('The file %s does not exist', file_name)
