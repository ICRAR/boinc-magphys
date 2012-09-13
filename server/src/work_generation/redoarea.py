#! /usr/bin/env python2.7
"""
Re-create the Observation file from the fits for an Area to allow it to be reprocessed.
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
import shutil
from config import db_login
from database.database_support import Galaxy, Area, PixelResult, FitsHeader
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from utils.writeable_dir import WriteableDir
from work_generation import FILTER_BANDS
from image.fitsimage import FitsImage
from config import django_image_dir

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser()
parser.add_argument('area_id', nargs=1, help='the area_id')
parser.add_argument('output_directory', action=WriteableDir, nargs=1, help='where observation files will be written to')
args = vars(parser.parse_args())

OUTPUT_DIR = args['output_directory']
AREA_ID = int(args['area_id'][0])
SIGMA = 0.1

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

def get_pixels(area):
    """
        Retrieves pixels from each pair of (x, y) coordinates specified in area top and bottom x and y values.
        Pixels are retrieved in the order specified in the global LAYER_ORDER list.
    """
    result = []
    for x in range(area.top_x, area.bottom_x):
        if x >= area.galaxy.dimension_x:
                continue
        for y in range(area.top_y, area.bottom_y):
            # Have we moved off the edge
            if y >= area.galaxy.dimension_y:
                continue

            pixels = []
            for layer in LAYER_ORDER:
                if layer == -1:
                    # The layer is missing
                    pixels.append(0)
                else:
                    # A vagary of PyFits/NumPy is the order of the x & y indexes is reversed
                    # See page 13 of the PyFITS User Guide
                    pixel = HDULIST[layer].data[y, x]
                    if math.isnan(pixel) or pixel == 0.0:
                        # A zero tells MAGPHYS - we have no value here
                        pixels.append(0)
                    else:
                        pixels.append(pixel)
            pixel = Pixel(x, y, pixels)
            for pxresult in area.pixelResults:
                if pxresult.x == x and pxresult.y == y:
                    pixel.pixel_id = pxresult.pxresult_id
                    result.append(pixel)
                    break

    return result


area = session.query(Area).filter("area_id=:area_id").params(area_id=AREA_ID).first()
if area == None:
    LOG.info(str(AREA_ID) + ' Area was not found')
else:
    galaxy = area.galaxy;
    
    filePrefixName = galaxy.name + "_" + str(galaxy.version_number)
    fitsFileName = filePrefixName + ".fits"
    
    image = FitsImage()
    fitsFile = image.get_file_path(django_image_dir, fitsFileName, False)
    
    HDULIST = pyfits.open(fitsFile, memmap=True)
    LAYER_COUNT = len(HDULIST)
    LAYER_ORDER = sort_layers(HDULIST, LAYER_COUNT)
    
    pixels = get_pixels(area)
    create_output_file(galaxy, area, pixels)
    
    HDULIST.close()
    LOG.info('Area ' + str(AREA_ID) + ' has been rebuilt')

