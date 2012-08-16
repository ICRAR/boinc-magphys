#! /usr/bin/env python2.7
"""
Create Observation files from the fits
"""
from __future__ import print_function
import argparse
import json

import logging
import math
import re
import datetime
import pyfits
import sys
from config import db_login
from database.database_support import Galaxy, Area, PixelResult, FitsHeader
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from utils.writeable_dir import WriteableDir
from work_generation import FILTER_BANDS
from image.fitsimage import FitsImage

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser()
parser.add_argument('FITS_file', nargs=1, help='the input FITS file containing the galaxy')
parser.add_argument('redshift', type=float, nargs=1, help='the redshift of the galaxy')
parser.add_argument('output_directory', action=WriteableDir, nargs=1, help='where observation files will be written to')
parser.add_argument('image_directory', action=WriteableDir, nargs=1, help='where the images will be written too')
parser.add_argument('galaxy_name', help='the name of the galaxy')
parser.add_argument('-rh', '--row_height', type=int, default=10, help='the row height')
parser.add_argument('-mp', '--min_pixels_per_file', type=int, default=30, help='the minimum number of pixels in the file')
args = vars(parser.parse_args())

status = {'calls__get_pixels': 0,
          'get_pixels_get_attempts': 0,
          'get_pixels_get_successful': 0,
          'get_pixels_values_returned': 0,
          'calls__create_area': 0,
          'create__area': 0,
          'create__pixel': 0}

# This value was suggested by David Thilker on 2012-06-05 as a starting point.
MIN_LIVE_CHANNELS_PER_PIXEL = 9

REDSHIFT = args['redshift'][0]
INPUT_FILE = args['FITS_file'][0]
OUTPUT_DIR = args['output_directory']
IMAGE_DIR = args['image_directory']
ROW_HEIGHT = int(args['row_height'])
MIN_PIXELS_PER_FILE = args['min_pixels_per_file']
GALAXY_NAME = args['galaxy_name']
SIGMA = 0.1

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

HDULIST = pyfits.open(INPUT_FILE, memmap=True)
LAYER_COUNT = len(HDULIST)

START_X = 0
START_Y = 0
END_Y = HDULIST[0].data.shape[0]
END_X = HDULIST[0].data.shape[1]

LOG.info("Image dimensions: %(x)d x %(y)d x %(z)d => %(pix).2f Mpixels" % {'x':END_X,'y':END_Y,'z':LAYER_COUNT,'pix':END_X*END_Y/1000000.0})

# Connect to the database - the login string is set in the database package
engine = create_engine(db_login)
Session = sessionmaker(bind=engine)
session = Session()
rollback = False

## ######################################################################## ##
##
## FUNCTIONS AND STUFF
##
## ######################################################################## ##

class Pixel:
    """
    A pixel
    """
    def __init__(self, x, y, pixels):
        self.x = x
        self.y = y
        self.pixels = pixels
        self.pixel_id = None

def store_fits_header(hdulist, galaxy_id):
    """
    Store the FITS headers we need to remember
    """
    header = hdulist[0].header
    for keyword in header:
        for pattern in HEADER_PATTERNS:
            if pattern.search(keyword):
                fh = FitsHeader()
                fh.galaxy_id = galaxy_id
                fh.keyword = keyword
                fh.value = header[keyword]
                session.add(fh)

def sort_layers(hdu_list, layer_count):
    """
    Look at the layers of a HDU and order them based on the effective wavelength stored in the header
    """
    names = []
    for layer in range(layer_count):
        hdu = hdu_list[layer]
        filter_name = hdu.header['MAGPHYSN']
        if filter_name is None:
            raise LookupError('The layer {0} does not have MAGPHYSN in it'.format(layer))
        names.append(filter_name)

        found_filter = False
        for name in FILTER_BANDS:
            if filter_name == name:
                found_filter = True
                break

        if not found_filter:
            raise LookupError('The filter {0} in the fits file is not expected'.format(filter_name))

    layers = []
    for filter_name in FILTER_BANDS:
        found_it = False
        for i in range(len(names)):
            if names[i] == filter_name:
                layers.append(i)
                found_it = True
                break
        if not found_it:
            layers.append(-1)

    return layers

def create_output_file(galaxy, area, pixels):
    """
        Write an output file for this area
    """
    pixels_in_area = len(pixels)
    data = [{'galaxy':galaxy.name, 'area_id':area.area_id, 'pixels':pixels_in_area, 'top_x':area.top_x, 'top_y':area.top_y, 'bottom_x':area.bottom_x, 'bottom_y':area.bottom_y,}]
    filename = '%(output_dir)s/%(galaxy)s_area%(area)s' % { 'galaxy':galaxy.name, 'output_dir':OUTPUT_DIR, 'area':area.area_id}
    outfile = open(filename, 'w')
    outfile.write('#  %(data)s\n' % { 'data': json.dumps(data) })

    row_num = 0
    for pixel in pixels:
        outfile.write('pix%(id)s %(pixel_redshift)s ' % {'id':pixel.pixel_id, 'pixel_redshift':galaxy.redshift})
        for value in pixel.pixels:
            outfile.write("{0}  {1}  ".format(value, value * SIGMA))

        outfile.write('\n')
        row_num += 1
    outfile.close()

def get_pixels(pix_x, pix_y):
    """
        Retrieves pixels from each pair of (x, y) coordinates specified in pix_x and pix_y.
        Returns pixels only from those coordinates where there is data in more than
        MIN_LIVE_CHANNELS_PER_PIXEL channels. Pixels are retrieved in the order specified in
        the global LAYER_ORDER list.
    """
    status['calls__get_pixels'] += 1

    result = []
    max_x = pix_x
    x = pix_x
    while x < END_X:
        for y in range(pix_y, pix_y + ROW_HEIGHT):
            # Have we moved off the edge
            if y >= END_Y:
                continue

            status['get_pixels_get_attempts'] += 1
            live_pixels = 0
            pixels = []
            for layer in LAYER_ORDER:
                if layer == -1:
                    # The layer is missing
                    pixels.append(0)
                else:
                    pixel = HDULIST[layer].data[x, y]
                    if math.isnan(pixel):
                        # A zero tells MAGPHYS - we have no value here
                        pixels.append(0)
                    else:
                        live_pixels += 1
                        pixels.append(pixel)

            if live_pixels >= MIN_LIVE_CHANNELS_PER_PIXEL:
                status['get_pixels_get_successful'] += 1
                status['get_pixels_values_returned'] += live_pixels
                result.append(Pixel(x, y, pixels))

        max_x = x
        if len(result) > MIN_PIXELS_PER_FILE:
            break

        x += 1

    return max_x, result

def create_areas(galaxy, pix_y):
    """
    Create a area - we try to make them squares, but they aren't as the images have dead zones
    """
    status['calls__create_area'] += 1
    pix_x = 0
    while pix_x < END_X:
        max_x, pixels = get_pixels(pix_x,pix_y)
        if len(pixels) > 0:
            status['create__area'] += 1
            area = Area()
            area.galaxy_id = galaxy.galaxy_id
            area.top_x = pix_x
            area.top_y = pix_y
            area.bottom_x = max_x
            area.bottom_y = pix_y + ROW_HEIGHT
            session.add(area)
            session.flush()

            for pixel in pixels:
                status['create__pixel'] += 1
                pixel_result = PixelResult()
                pixel_result.galaxy_id = galaxy.galaxy_id
                pixel_result.area_id = area.area_id
                pixel_result.x = pixel.x
                pixel_result.y = pixel.y
                session.add(pixel_result)
                session.flush()

                pixel.pixel_id = pixel_result.pxresult_id

            # Write the pixels
            create_output_file(galaxy, area, pixels)

        pix_x = max_x + 1

def break_up_galaxy(galaxy):
    for pix_y in range(START_Y, END_Y, ROW_HEIGHT):
        str = "Scanned %(pct_done)3d%% of image" % { 'pct_done':100*(pix_y-START_Y)/(END_Y-START_Y) }
        print(str, end="\r")
        sys.stdout.flush()
        create_areas(galaxy, pix_y)

## ######################################################################## ##
##
## Where it all starts
##
## ######################################################################## ##

#Here, it might be useful to assert that there are 12 input layers/channels/HDUs
#print "List length: %(#)d" % {'#': len(HDULIST)}

if GALAXY_NAME is not None:
    object_name = GALAXY_NAME
else:
    object_name = HDULIST[0].header['OBJECT']
LOG.info("Work units for: %(object)s" % { "object":object_name } )

# Create and save the object
galaxy = Galaxy()
galaxy.name = object_name
galaxy.dimension_x = END_X
galaxy.dimension_y = END_Y
galaxy.dimension_z = LAYER_COUNT
galaxy.redshift = REDSHIFT
galaxy.create_time = datetime.datetime
session.add(galaxy)

# Flush to the DB so we can get the id
session.flush()

LOG.info("Wrote %(object)s to database" % { 'object':galaxy.name })

# Store the fits header
store_fits_header(HDULIST, galaxy.galaxy_id)
LAYER_ORDER = sort_layers(HDULIST, LAYER_COUNT)
break_up_galaxy(galaxy)

LOG.info("\nRun status\n")
for key in sorted(status.keys()):
    LOG.info("%(key)30s %(val)s" % { 'key':key, 'val':status[key] })

if rollback:
    session.rollback()
else:
    image = FitsImage()
    image.buildImage(INPUT_FILE, IMAGE_DIR, object_name, "asinh", False, False, False)
    session.commit()

LOG.info("\nDone")
