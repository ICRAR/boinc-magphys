import math
import pyfits
import sys
from database_support import *

if(len(sys.argv) != 2):
	print "usage:   %(me)s FITS_file" % {'me':sys.argv[0]}
	print "example: %(me)s /Users/astrogeek/Documents/ICRAR/POGS_NGC628_v3.fits" % {'me':sys.argv[0]}
	sys.exit(-10)
	
MIN_LIVE_CHANNELS_PER_PIXEL = 3;
INPUT_FILE = '/Users/perh/Dropbox/Documents/Work/ThoughtWorks/Projects/ICRAR/POGS_NGC628_v3.fits';
GRID_SIZE = 5

# TODO:    this should be gleaned from the FITS file
# WARNING: START_X and/or START_Y should be zero or some calculations will
#          be off; these should probably be removed before going "live"

START_X = 1900
START_Y = 1900
END_X = 2000
END_Y = 2000

HDULIST = pyfits.open(INPUT_FILE);
LAYER_COUNT = len(HDULIST)


## ######################################################################## ##
## 
## FUNCTIONS AND STUFF
## 
## ######################################################################## ##

class Coordinate:
	def __init__(self, x_coord, y_coord):
		self.x = x_coord
		self.y = y_coord
	def __str__(obj):
		return "<%(x)s, %(y)s>" % {'x':obj.x,'y':obj.y}

def get_pixels(pix_x, pix_y):
#	print "Getting pixels in <%(x)s, %(y)s>" % {'x':pix_x, 'y':pix_y} 
	result = []
	for x in pix_x:
		if x >= END_X:
			continue;
		for y in pix_y:
			if y >= END_Y:
				continue;

			pixels = [HDULIST[layer].data[x, y] for layer in range(LAYER_COUNT)]
			live_pixels = 0
			for p in pixels:
				if not math.isnan(p):
					live_pixels += 1

			# For now, only output pixels where MIN_LIVE_CHANNELS_PER_PIXEL or more channels have data
			# Are all channels created equally, or should different channels have different "weights" so that, for example,
			# we might discard a pixel that have data for 10 channels but is missing UV, while retaining pixels where we have
			# data for only, say, 6 pixels but that has UV? Discussion with Kevin?
			if live_pixels >= MIN_LIVE_CHANNELS_PER_PIXEL:
				result.append(Pixel({'x':x,'y':y,'pixel_values':" ".join(map(str, pixels))}))

	return result

def create_square(object, pix_x, pix_y):
	pixels = get_pixels([pix_x], range(pix_y, pix_y+GRID_SIZE))
	if len(pixels)>0:
		pixels.extend(get_pixels(range(pix_x+1, pix_x+GRID_SIZE), range(pix_y, pix_y+GRID_SIZE)))
		
		square = Square({'object_id':object.id, 'top_x':pix_x, 'top_y':pix_y, 'size':GRID_SIZE}).save()
		
		for pixel in pixels:
#			p = pixel.keys()[0]
			pixel.object_id = object.id
			pixel.square_id = square.id
			pixel.save()
#			px = Pixel({'object_id':object.id,'square_id':square.id,'x':p.x,'y':p.y,'pixel_values':" ".join(map(str, pixel[p]))}).save()

		return GRID_SIZE
	else:
		return 1

def squarify(object):
	for pix_y in range(START_Y, END_Y, GRID_SIZE):
		print "Scanned %(pct_done)3d%% of image" % { 'pct_done':100*(pix_y-START_Y)/(END_Y-START_Y) }
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

object_name = HDULIST[0].header['OBJECT'] + "3"
print "Work units for: %(object)s" % { "object":object_name } 

# Create and save the object
object = Object({'name':object_name, 'dimension_x':END_X, 'dimension_y':END_Y, 'dimension_z':LAYER_COUNT})
object.save()

print "Wrote %(object)s to database" % { 'object':object }

squares = squarify(object)

print "Done"
# Uncomment to print general information about the file to stdout
#HDULIST.info()

