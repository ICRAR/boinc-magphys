from __future__ import print_function
import math
import pyfits
import sys
import cProfile
from database_support import *

if(len(sys.argv) < 2):
	print("usage:   %(me)s FITS_file [start_x start_y end_x end_y]" % {'me':sys.argv[0]})
	print("         specify square cutout parameters only in development mode")
	print("example: %(me)s /home/ec2-user/POGS_NGC628_v3.fits" % {'me':sys.argv[0]})
	sys.exit(-10)

status = {}
status['calls__get_pixels'] = 0
status['get_pixels_get_attempts'] = 0 		# Number of attempts to retrieve (x,y) pixels
status['get_pixels_get_successful'] = 0 	# Number of pixels where more than MIN_LIVE_CHANNELS_PER_PIXEL contained data
status['get_pixels_values_returned'] = 0 	# Number of individual pixel values returned
status['calls__create_square'] = 0 
status['create__square'] = 0
status['create__pixel'] = 0
	
# TODO:    this should be gleaned from the FITS file
# WARNING: START_X and/or START_Y should be zero or some calculations will
#          be off; these should probably be removed before going "live"
START_X = 0
START_Y = 0
END_X = 3840
END_Y = 3840
if len(sys.argv) > 5:
	START_X = int(sys.argv[2])
	START_Y = int(sys.argv[3])
	END_X = int(sys.argv[4])
	END_Y = int(sys.argv[5])
	print("\nDEVELOPMENT MODE: cutting out square (%(s_x)d, %(s_y)d) to (%(e_x)d, %(e_y)d)\n" % {
		's_x':START_X,'s_y':START_Y,'e_x':END_X,'e_y':END_Y})

# This value was suggested by David Thilker on 2012-06-05 as a starting point.	
MIN_LIVE_CHANNELS_PER_PIXEL = 9
INPUT_FILE = sys.argv[1]
GRID_SIZE = 10

HDULIST = pyfits.open(INPUT_FILE)
LAYER_COUNT = len(HDULIST)
HARD_CODED_REDSHIFT = 0.0


## ######################################################################## ##
## 
## FUNCTIONS AND STUFF
## 
## ######################################################################## ##

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

def get_pixels(pix_x, pix_y):
	"""
		Retrieves pixels from each pair of (x, y) coordinates specified in pix_x and pix_y. 
		Returns pixels only from those coordinates where there is data in more than 
		MIN_LIVE_CHANNELS_PER_PIXEL channels. Pixels are retrieved in the order specified in
		the global LAYER_ORDER list.
	"""
	status['calls__get_pixels'] += 1;
#	print "Getting pixels in <%(x)s, %(y)s>" % {'x':pix_x, 'y':pix_y} 
	result = []
	for x in pix_x:
		if x >= END_X:
			continue;
		for y in pix_y:
			if y >= END_Y:
				continue;

			status['get_pixels_get_attempts'] += 1;
#			pixels = [HDULIST[layer].data[x, y] for layer in range(LAYER_COUNT)]
			pixels = [HDULIST[layer].data[x, y] for layer in LAYER_ORDER]
			live_pixels = 0
			for p in pixels:
				if not math.isnan(p):
					live_pixels += 1

			if live_pixels >= MIN_LIVE_CHANNELS_PER_PIXEL:
				status['get_pixels_get_successful'] += 1;
				status['get_pixels_values_returned'] += live_pixels;
				result.append(Pixel({'x':x,'y':y,'redshift':HARD_CODED_REDSHIFT,'pixel_values':" ".join(map(str, pixels))}))

	return result

def create_square(object, pix_x, pix_y):
	status['calls__create_square'] += 1;
	pixels = get_pixels([pix_x], range(pix_y, pix_y+GRID_SIZE))
	if len(pixels)>0:
		pixels.extend(get_pixels(range(pix_x+1, pix_x+GRID_SIZE), range(pix_y, pix_y+GRID_SIZE)))
		
		status['create__square'] += 1;
		square = Square({'object_id':object.id, 'top_x':pix_x, 'top_y':pix_y, 'size':GRID_SIZE}).save()
		
		for pixel in pixels:
			status['create__pixel'] += 1;
			pixel.object_id = object.id
			pixel.square_id = square.id
			pixel.write() # Performance optimisation: write() does not retrieve ID after INSERT

		return GRID_SIZE
	else:
		return 1

def squarify(object):
	for pix_y in range(START_Y, END_Y, GRID_SIZE):
		str = "Scanned %(pct_done)3d%% of image" % { 'pct_done':100*(pix_y-START_Y)/(END_Y-START_Y) }
		print(str, end="\r")
		sys.stdout.flush()
		pix_x = START_X
		while pix_x < END_X:
			pix_x += create_square(object, pix_x, pix_y)

## ######################################################################## ##
## 
## Where it all starts
## 
## ######################################################################## ##

#Here, it might be useful to assert that there are 12 input layers/channels/HDUs
#print "List length: %(#)d" % {'#': len(HDULIST)} 

object_name = HDULIST[0].header['OBJECT']
print("Work units for: %(object)s" % { "object":object_name } )

# Create and save the object
object = Object({'name':object_name, 'dimension_x':END_X, 'dimension_y':END_Y, 'dimension_z':LAYER_COUNT})
object.save()

print("Wrote %(object)s to database" % { 'object':object })

LAYER_ORDER = sort_layers(HDULIST, LAYER_COUNT)

squares = squarify(object)

print("\nRun status")
for key in sorted(status.keys()):
	print("%(key)30s %(val)s" % { 'key':key, 'val':status[key] })

Database.getConnection().commit()
print("\nDone")
# Uncomment to print general information about the file to stdout
#HDULIST.info()
