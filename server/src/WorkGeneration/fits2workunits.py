import math
import pyfits
import numpy as np

MIN_LIVE_CHANNELS_PER_PIXEL = 3;
INPUT_FILE = '/Users/perh/Dropbox/Documents/Work/ThoughtWorks/Projects/ICRAR/POGS_NGC628_v3.fits';
GRID_SIZE = 10

# The file is 3840x3840. Right now only looking at a small square where there is data
START_X = 2100
START_Y = 1800
END_X = 2200
END_Y = 2000


##
##
## FUNCTIONS AND STUFF
## 
##

def get_pixels(pix_x, pix_y, layer_count):
	#print "Extracting pixels from (%(pix_x)s, %(pix_y)s)" % {'pix_x':pix_x, 'pix_y':pix_y}
	result = []
	for x in pix_x:
		for y in pix_y:
			pixels = [hdulist[layer].data[x, y] for layer in range(layer_count)]
			live_pixels = 0
			for p in pixels:
				if not math.isnan(p):
					live_pixels += 1

			# For now, only output pixels where MIN_LIVE_CHANNELS_PER_PIXEL or more channels have data
			# Are all channels created equally, or should different channels have different "weights" so that, for example,
			# we might discard a pixel that have data for 10 channels but is missing UV, while retaining pixels where we have
			# data for only, say, 6 pixels but that has UV? Discussion with Kevin?
			if live_pixels >= MIN_LIVE_CHANNELS_PER_PIXEL:
				#print "%(galaxy)s__%(x)d_%(y)d " % { 'galaxy':object_name, 'x':x, 'y':y}
				result.append(pixels)
		return result
	
def alg1(layer_count):
	squares = []
	
	for pix_x in range(START_X, END_X, GRID_SIZE):
#		print "at x=%(x)d" % { 'x':pix_x }
		for pix_y in range(START_Y, END_Y, GRID_SIZE):
			pixels = get_pixels(range(pix_x, pix_x+GRID_SIZE), range(pix_y, pix_y+GRID_SIZE), layer_count)
			if len(pixels)>0:
				print "Okay, there are pixels somewhere here: %(pixels)s" % { 'pixels': pixels }
				squares.append([pix_x, pix_y]);

	return squares
	
##
##
## Where it all starts
##
##

hdulist = pyfits.open(INPUT_FILE);
print "List length: %(#)d" % {'#': len(hdulist)} #Here, it might be useful to assert that there are 12 input layers/channels/HDUs

layer_count = len(hdulist)
object_name = hdulist[0].header['OBJECT']

squares = alg1(layer_count)
print squares
# Uncomment to print general information about the file to stdout
#hdulist.info()

