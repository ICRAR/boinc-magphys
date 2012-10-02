#! /usr/bin/env python2.7
"""
Check the characteristics of the fits file
"""
import argparse
import logging
import os
import pyfits
from work_generation import HEADER_PATTERNS

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser()
parser.add_argument('file_names', nargs='+', help='the files to be checked')
args = vars(parser.parse_args())

for file_name in args['file_names']:
    if os.path.isfile(file_name):
        LOG.info('Check %s', file_name)

        hdu_list = pyfits.open(file_name, memmap=True)
        layer_count = len(hdu_list)

        end_y = hdu_list[0].data.shape[0]
        end_x = hdu_list[0].data.shape[1]

        LOG.info("Image dimensions: %(x)d x %(y)d x %(z)d => %(pix).2f Mpixels" % {'x':end_x,'y':end_y,'z':layer_count,'pix':end_x*end_y/1000000.0})

        # Read the fits headers
        for layer in range(layer_count):
            header = hdu_list[layer].header
            for keyword in header:
                found_pattern = False
                for pattern in HEADER_PATTERNS:
                    if pattern.search(keyword):
                        LOG.info('** Layer %d - %s: %s', layer, keyword, header[keyword])
                        found_pattern = True
                        break

                if not found_pattern:
                    LOG.info('Layer %d - %s: %s', layer, keyword, header[keyword])

    else:
        LOG.info('The file %s does not exist', file_name)
