from __future__ import print_function
import datetime
import math
import pyfits
import sys
from database.database_support import Galaxy, Square, PixelResult
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


if len(sys.argv) < 3:
    print("usage:   %(me)s FITS_file output_directory [galaxy_name]" % {'me':sys.argv[0]})
    print("         specify square cutout parameters only in development mode")
    print("example: %(me)s /home/ec2-user/POGS_NGC628_v3.fits /home/ec2-user/f2wu" % {'me':sys.argv[0]})
    sys.exit(-10)

status = {}
status['calls__get_pixels'] = 0
status['get_pixels_get_attempts'] = 0 		# Number of attempts to retrieve (x,y) pixels
status['get_pixels_get_successful'] = 0 	# Number of pixels where more than MIN_LIVE_CHANNELS_PER_PIXEL contained data
status['get_pixels_values_returned'] = 0 	# Number of individual pixel values returned
status['calls__create_square'] = 0
status['create__square'] = 0
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

print("Image dimensions: %(x)d x %(y)d x %(z)d => %(pix).2f Mpixels" % {'x':END_X,'y':END_Y,'z':LAYER_COUNT,'pix':END_X*END_Y/1000000.0})

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

def sort_layers(hdu_list, layer_count):
    """
    Look at the layers of a HDU and order them based on the effective wavelength stored in the header
    """
    dictionary = {}

    for layer in range(layer_count):
        hdu = hdu_list[layer]
        header = hdu.header
        lamda = header['MAGPHYSL']
        if lamda is None:
            raise LookupError('No MAGPHYS Lamda value found')
        else:
            dictionary[lamda] = layer

    items = dictionary.items()
    items.sort()
    return [value for key, value in items]

def create_output_file(galaxy, square, pixels):
    """
    Write an output file for this square
    """
    pixels_in_square = len(pixels)
    filename = '%(output_dir)s/%(galaxy)s__wu%(square)s' % { 'galaxy':galaxy.name, 'output_dir':OUTPUT_DIR, 'square':square.square_id}
    outfile = open(filename, 'w')
    outfile.write('#  This workunit contains observations for galaxy %(galaxy)s. ' % { 'galaxy':square.getObject().name })
    outfile.write('%(square)s contains %(count)s pixels with above-threshold observations\n' % {
        'square':square.square_id, 'count':pixels_in_square })

    row_num = 0
    for pixel in pixels:
        outfile.write('pix%(id)s %(pixel_redshift)s ' % {'id':pixel.pixel_id, 'pixel_redshift':galaxy.redshift})
        for value in pixel.pixels:
            outfile.write("{0} {1}".format(value, value * SIGMA))

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
    status['calls__get_pixels'] += 1;

    result = []
    for x in pix_x:
        if x >= END_X:
            continue
        for y in pix_y:
            if y >= END_Y:
                continue

            status['get_pixels_get_attempts'] += 1
            pixels = [HDULIST[layer].data[x, y] for layer in LAYER_ORDER]
            pixel_tuples = []
            live_pixels = 0
            for p in pixels:
                if not math.isnan(p):
                    live_pixels += 1
                    pixel_tuples.extend(p)

            if live_pixels >= MIN_LIVE_CHANNELS_PER_PIXEL:
                status['get_pixels_get_successful'] += 1
                status['get_pixels_values_returned'] += live_pixels
                result.append(Pixel(x, y, pixel_tuples))

    return result

def create_square(galaxy, pix_x, pix_y):
    status['calls__create_square'] += 1
    pixels = get_pixels([pix_x], range(pix_y, pix_y+GRID_SIZE))
    if len(pixels) > 0:
        pixels.extend(get_pixels(range(pix_x+1, pix_x+GRID_SIZE), range(pix_y, pix_y+GRID_SIZE)))

        status['create__square'] += 1
        square = Square()
        square.galaxy_id = galaxy.galaxy_id
        square.top_x = pix_x
        square.top_y = pix_y
        square.size = GRID_SIZE
        square.wu_generated = datetime.datetime
        session.add(square)
        session.flush()

        for pixel in pixels:
            status['create__pixel'] += 1
            pixel_result = PixelResult()
            pixel_result.galaxy_id = galaxy.galaxy_id
            pixel_result.square_id = square.square_id
            pixel_result.x = pixel.x
            pixel_result.y = pixel.y
            session.add(pixel_result)
            session.flush()

            pixel.pixel_id = pixel_result.pixel_id

        # Write the pixels
        create_output_file(galaxy, square, pixels)

        return GRID_SIZE
    else:
        return 1

def squarify(galaxy):
    for pix_y in range(START_Y, END_Y, GRID_SIZE):
        str = "Scanned %(pct_done)3d%% of image" % { 'pct_done':100*(pix_y-START_Y)/(END_Y-START_Y) }
        print(str, end="\r")
        sys.stdout.flush()
        pix_x = START_X
        while pix_x < END_X:
            pix_x += create_square(galaxy, pix_x, pix_y)

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
print("Work units for: %(object)s" % { "object":object_name } )

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

print("Wrote %(object)s to database" % { 'object':galaxy })

LAYER_ORDER = sort_layers(HDULIST, LAYER_COUNT)
squares = squarify(galaxy)

print("\nRun status")
for key in sorted(status.keys()):
    print("%(key)30s %(val)s" % { 'key':key, 'val':status[key] })

if rollback:
    session.rollback()
else:
    session.commit()

print("\nDone")
