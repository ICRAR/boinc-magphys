import math
import pyfits
import numpy as np

MIN_LIVE_CHANNELS_PER_PIXEL = 3;
INPUT_FILE = '/Users/perh/Dropbox/Documents/Work/ThoughtWorks/Projects/ICRAR/POGS_NGC628_v3.fits';
GRID_SIZE = 5	

# The file is 3840x3840. Right now only looking at a small square where there is data
START_X = 1800
START_Y = 1800
END_X = 1900
END_Y = 1900

HDULIST = pyfits.open(INPUT_FILE);
LAYER_COUNT = len(HDULIST)


##
##
## FUNCTIONS AND STUFF
## 
##

def get_pixels(pix_x, pix_y):
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
#				print "%(galaxy)s__%(x)d_%(y)d " % { 'galaxy':object_name, 'x':x, 'y':y}

# DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG
# DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG
# 
# To make it easier to see where the pixels come from, simply appending the coordinates for now.
# This will obviously not work!
#
# DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG
# DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG

#				result.append(pixels)
				result.append([x, y])
	return result
	
def squarify_0():
	squares = []
	for pix_x in range(START_X, END_X, GRID_SIZE):
		for pix_y in range(START_Y, END_Y, GRID_SIZE):
			squares.append([pix_x, pix_y]);
	return squares
	
def squarify_1():
	squares = []
	for pix_x in range(START_X, END_X, GRID_SIZE):
		for pix_y in range(START_Y, END_Y, GRID_SIZE):
			pixels = get_pixels(range(pix_x, pix_x+GRID_SIZE), range(pix_y, pix_y+GRID_SIZE))
			if len(pixels)>0:
				squares.append([pix_x, pix_y]);
	return squares
	
def squarify_2():
	squares = []
	for pix_y in range(START_Y, END_Y, GRID_SIZE):
		pix_x = START_X
		while pix_x < END_X:
			pixels = get_pixels([pix_x], range(pix_y, pix_y+GRID_SIZE))
			if len(pixels)>0:
				squares.append([pix_x, pix_y]);
				pix_x+=GRID_SIZE;
			else:
				pix_x+=1
	return squares

def verify(squares):
	result = []
	distribution = [0 for i in range(GRID_SIZE * GRID_SIZE + 1)]
	print "Verifying algorithm that returned %(x)d squares" % {'x':len(squares)}
	for square in squares:
		pixels = get_pixels(range(square[0], square[0]+GRID_SIZE), range(square[1], square[1]+GRID_SIZE))
		pixel_count = len(pixels)
		distribution[pixel_count] += 1
		if pixel_count>0:
			result.extend(pixels)

	for i in range(GRID_SIZE * GRID_SIZE + 1):
		print " -- %(pixels)2d pixels: %(count)7d squares" % { 'pixels':i, 'count':distribution[i] }
	return "Found %(count)d pixels" % {'count':len(result) }
	
##
##
## Where it all starts
##
##

#Here, it might be useful to assert that there are 12 input layers/channels/HDUs
#print "List length: %(#)d" % {'#': len(HDULIST)} 

object_name = HDULIST[0].header['OBJECT']


print verify(squarify_2())
print "================================ END OF OUTPUT ================================"

# Uncomment to print general information about the file to stdout
#HDULIST.info()

