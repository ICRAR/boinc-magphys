from __future__ import print_function

import logging
import math
import pyfits
import sys
from database.database_support import Galaxy, Area, PixelResult
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from work_generation import FILTER_BANDS

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

if len(sys.argv) < 3:
    print("usage:   %(me)s FITS_file output_directory [galaxy_name]" % {'me':sys.argv[0]})
    print("example: %(me)s /home/ec2-user/POGS_NGC628_v3.fits /home/ec2-user/f2wu" % {'me':sys.argv[0]})
    sys.exit(-10)

status = {}
status['calls__get_pixels'] = 0
status['get_pixels_get_attempts'] = 0 		# Number of attempts to retrieve (x,y) pixels
status['get_pixels_get_successful'] = 0 	# Number of pixels where more than MIN_LIVE_CHANNELS_PER_PIXEL contained data
status['get_pixels_values_returned'] = 0 	# Number of individual pixel values returned
status['calls__create_area'] = 0
status['create__area'] = 0
status['create__pixel'] = 0

# This value was suggested by David Thilker on 2012-06-05 as a starting point.
MIN_LIVE_CHANNELS_PER_PIXEL = 9
INPUT_FILE = sys.argv[1]
OUTPUT_DIR = sys.argv[2]
SIGMA = 0.1
GRID_SIZE = 7

HDULIST = pyfits.open(INPUT_FILE, memmap=True)
LAYER_COUNT = len(HDULIST)
HARD_CODED_REDSHIFT = 0.0

START_X = 0
START_Y = 0
END_Y = HDULIST[0].data.shape[0]
END_X = HDULIST[0].data.shape[1]

LOG.info("Image dimensions: %(x)d x %(y)d x %(z)d => %(pix).2f Mpixels" % {'x':END_X,'y':END_Y,'z':LAYER_COUNT,'pix':END_X*END_Y/1000000.0})

# Connect to the database
login = "mysql://root:@localhost/magphys"
engine = create_engine(login)
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
    filename = '%(output_dir)s/%(galaxy)s__wu%(area)s' % { 'galaxy':galaxy.name, 'output_dir':OUTPUT_DIR, 'area':area.area_id}
    outfile = open(filename, 'w')
    outfile.write('#  This workunit contains observations for galaxy %(galaxy)s. ' % { 'galaxy':galaxy.name })
    outfile.write('Area %(area)s (%(top_x)s,%(top_y)s) to (%(bottom_x)s,%(bottom_y)s) contains %(count)s pixels with above-threshold observations.\n' % {
        'area':area.area_id, 'count':pixels_in_area, 'top_x':area.top_x, 'top_y':area.top_y, 'bottom_x':area.bottom_x, 'bottom_y':area.bottom_y,})

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
    max_y = pix_y
    for x in range(pix_x, pix_x + GRID_SIZE):
        if x >= END_X:
            # Have we moved off the edge
            continue
        for y in range(pix_y, pix_y + GRID_SIZE):
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
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y

    return max_x, max_y, result

def create_area(galaxy, pix_y):
    """
    Create a area - we try to make them squares, but they aren't as the images have dead zones
    """
    status['calls__create_area'] += 1
    for pix_x in range(START_X, END_X, GRID_SIZE):
        max_x, max_y, pixels = get_pixels(pix_x, pix_y)
        if len(pixels) > 0:
            status['create__area'] += 1
            area = Area()
            area.galaxy_id = galaxy.galaxy_id
            area.top_x = pix_x
            area.top_y = pix_y
            area.bottom_x = max_x
            area.bottom_y = max_y
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

def squarify(galaxy):
    for pix_y in range(START_Y, END_Y, GRID_SIZE):
        str = "Scanned %(pct_done)3d%% of image" % { 'pct_done':100*(pix_y-START_Y)/(END_Y-START_Y) }
        print(str, end="\r")
        sys.stdout.flush()
        create_area(galaxy, pix_y)

## ######################################################################## ##
##
## Where it all starts
##
## ######################################################################## ##

#Here, it might be useful to assert that there are 12 input layers/channels/HDUs
#print "List length: %(#)d" % {'#': len(HDULIST)}

if len(sys.argv) > 3:
    object_name = sys.argv[3]
else:
    object_name = HDULIST[0].header['OBJECT']
LOG.info("Work units for: %(object)s" % { "object":object_name } )

# Create and save the object
galaxy = Galaxy()
galaxy.name = object_name
galaxy.dimension_x = END_X
galaxy.dimension_y = END_Y
galaxy.dimension_z = LAYER_COUNT
galaxy.redshift = HARD_CODED_REDSHIFT
session.add(galaxy)

# Flush to the DB so we can get the id
session.flush()

LOG.info("Wrote %(object)s to database" % { 'object':galaxy.name })

LAYER_ORDER = sort_layers(HDULIST, LAYER_COUNT)
squarify(galaxy)

LOG.info("\nRun status")
for key in sorted(status.keys()):
    print("%(key)30s %(val)s" % { 'key':key, 'val':status[key] })

if rollback:
    session.rollback()
else:
    session.commit()

LOG.info("\nDone")
